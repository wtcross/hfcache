# WEB-033: Close named acceptance gaps using direct installed job/recovery workflows and the affected format/profile drills

| Field | Value |
| --- | --- |
| Status | completed |
| Plan | [Job recovery and archive writes](../2026-11-03-plan-job-recovery-and-archive-writes.md) |
| Depends on | API-019, WEB-032, OPS-027 |
| Execution | `gpt-6.1-sol` / `medium`; explicit task-agent setting required |

## Scope and acceptance

Close named acceptance gaps using direct installed job/recovery workflows and the affected format/profile drills; reuse valid unchanged evidence and update human guides, without building a new harness.

The parent plan's applicable scope, acceptance criteria and safety prerequisites
are binding. No remote pushes, image publication, release tags, automatic
schedules, unrelated permissions, archive initialization, manual archive writes,
reboots, NFS disconnection or other-host effects are authorized.

## Contracts, invariants, and ADRs

Review the parent plan's affected contract and decision list progressively.
Record exact reviewed IDs, amendments and any new decision before completion.

Reviewed INV-003, INV-007, INV-020, INV-021 and INV-023, ADR121 and the executable
ADR164/165 amendments. The native masked-unit repair corrects conformance with
the existing legacy-mask and quiescence requirements; ADR121 and the deployment
contract clarify that recognition without adding an invariant or architectural
decision. Permanent fences, actual executor review, independent protected
effects, source/installed evidence separation and current-boot writer scope stay
binding. Final source-bound and installed review is complete: INV-003/007/020/021/023
and ADR121/150/164/165 agree with the qualified native/rootless behavior. The
existing records are amended for conformance repairs; no runtime dependency,
new architectural decision, broad capability or weakened hardening is introduced.

## Validation

The finite matrix below scopes changed installed boundaries. Earlier unchanged
Library/configuration/MCP/domain workflows retain their original evidence and
scope; a new aggregate or historical rollout replay is not required. Source
evidence is never promoted to installed evidence.

| Changed requirement | Smallest meaningful check | Required gate | Evidence/result |
| --- | --- | --- | --- |
| Readiness and original-intent browser recovery | Actual installed Caddy/TLS/API/private worker/helper, native and rootless, root and `/management`, fresh Chromium/Firefox/WebKit contexts; causal refusal, saved unknown review/retirement, retained handles and GET-only visible reconciliation | `scripts/check.sh --require-web` | Native all6 availability/migration/retirement/reload and lost-ack recovery pass; Chromium both-prefix causal refusal and preserved Firefox original GET recovery pass; rootless source10 six-context recovery and six-context lost-ack observations pass; source11 writer GET recovery and restart/rollback preserve original successful results |
| Permanent disposition and browser migration | Exact predecessor0.3.1/c23abba reader refuses new admission/state without mutation; capable current reader observes original IDs/fences; browser1 migration preserves handles and old browser refuses browser2 | Same gate | Native exact c23abba populated predecessor/current readers and browser migration/refusal pass; unchanged parser/registry bytes reused explicitly. Actual rootless epoch3 activation/current-reader restoration and source10 six-context migrations pass; no claim of old-binary HTTP/profile execution |
| Runtime2/manifest2 writer selection and rollback | Installed immutable guarded/manual siblings, mismatched/old reader refusal, preserved original locks/state, drained read-only selection and rollback | Same gate | OPS-027 predecessor/source proof retained; actual immutable source11 manual selection/application writes, full executor drain, RO guarded rollback, genuine authority bootstrap, confined restart and original-result reads pass |
| Offline activation and companion authority | Actual native transient masks/private runtime and rootless selected-role offline activation, owner/label/restart/no-recreation, admission blocked until capable authority exists | Same gate | Actual native and rootless epoch3 offline isolation/whole authority restoration pass; source11 missing original companion exits20 before engine start, restores same inode, and drained regular-role restart passes |
| Confined rootless writer roles | Actual Enforcing API/worker application-path writes and helper/observer denials, identity/MCS/mount joins, fail-closed mismatches and capacity/interlock behavior | Same gate | Actual source11 Enforcing API Sync/private worker full Verify writes, original-lock waiting/release, sentinel/capacity negatives and exact confined role/mount joins pass; helper/observer denial evidence retained with unchanged vectors. Copied strict policy retains38 failures and is never called a strict pass |
| Reproduced native switch refusal for required legacy masks | Real installed official switch refuses masked/inactive `hfcache-sync.timer`; accept only explained masked/inactive units while retaining process/task/cgroup and original-lock guards; repeat actual switch after focused regression checks | Same gate | Original switch1 failure retained; source2 actual switch2 passes with all four masks retained |
| Reproduced native offline credential-metadata refusal | Actual selected installer refuses canonical API because systemctl renders structured credential arrays as `[unprintable]`; inspect the two fixed system-bus typed arrays, retain canonical/no-dropin/source/revision guards, then repeat official preparation from a newly gated immutable candidate | Same gate after repair | Original offline1 failure retained without transient, companion or backup; structured credential-array repair retained through strict gate5 and actual native offline preparation/isolation passes (evidence below) |
| Reproduced native reviewed-retirement coordination-parent refusal | Actual first retirement POST503 and helper PermissionError against the canonical service-owned0700 runtime parent; qualify a bounded metadata-child repair without changing permissions/caps or thread credentials | Same strict gate after any technical repair | Actual attempt2/metadata evidence retained; named high-effort source repair, strict gate5 and actual installed Enforcing native retirement pass |
| Reproduced native whole-executor kernel-process traversal refusal | Actual original retirement503 advances past repaired companion metadata, then confined native observe-peer cannot open `/proc/2` directory for read while scanning UID membership; preserve complete executor proof and SELinux/hardening | New strict gate only if technical repair changes final inputs | Availability3 original response/seed and exact kernel_t directory read AVC4743 retained; minimal repair395 focused tests, strict gate5, installed Enforcing native retirement and helper/observer payload denials pass |
| Reproduced rootless vendor-broker status refusal | Original installed user-manager journal joins helper_t fixed broker query to dbusd_unit_file_t service/status denial; preserve original key/503 and grant only that metadata type read/status, never control | New strict gate after repair | First Chromium/root readiness/migration passes, explicit retirement503 HFAPI015; focused red/green regression and64 policy tests pass; subsequent strict gate12, actual confined component and rootless retirement qualification pass |
| Reproduced protected PAM companion identity refusal | Actual source8 retirement reaches closed inert scan, then UID983 cannot read protected stock sd-pam executable link; verify the specific protected user-manager/PAM lineage without new capabilities or generic permission-error fallback | Fresh strict gate after focused actual-target proof | Source8 original503 and independent UID983/process/unit/maps/signal metadata preserved; closed typed PAM proof, source9 actual confined component5, source10 full five-inert component2, strict gate12 and installed rootless retirement pass |

Preserve raw failures. Do not invoke the optional instrumented functional runner.
REL-018 owns the final release `--with-build` gate. This task's strict gate runs
on its final technical inputs and also satisfies its default gate requirement;
an installed defect requiring another technical change requires a new gate.
Actual production NFS identity/capacity/reserve/preflight, transition and original
pilot/backfill handles remain OPS-029; production selection remains OPS-028.

## Execution notes and handoff

Activated 2026-11-03 by the user's explicit end-to-end implementation instruction.
Protected deployment, controlled writable transition, selected Sync and refresh
pilots and bounded metadata backfill are authorized after the reviewed safety
prerequisites. Scope is this host/current boot with fail-closed manual startup
permitted; unattended boot acceptance remains separate.

2026-11-03 startup: clean `main` at `7894540`; source gate19 already green.
Execution uses the fresh task agent explicitly selected as `gpt-6.1-sol` /
`medium` by the coordinator, rather than an inferred client default.
The finite matrix is recorded before implementation. Root/home capacity is
approximately1.18GB/89MB and available RAM4.18GB with swap full. No new image,
large copy or fixture is started before a bounded resource/launch review. Existing
fresh-fixture2 remains live and untouched; only its immutable read-only backing
may be considered for a disjoint owned overlay after fresh identity/FD checks.

The archive-initialization prohibition applies to the existing production archive
and inherited unknown payload. The plan's throwaway-format acceptance permits
application creation of a new owned fixture with its own UUID/path, as reviewed
by the coordinator; it never permits initializing the live archive. The owned
guest uses no host shares or NAS. Its new local loopback-NFS fixture is
`/var/lib/hfcache-web033-export`, UUID
`fc118f3e-2b23-43e9-bc7c-24795b155031`, initially mounted at
`/mnt/hfcache-web033-initialize` for application creation. The inherited archive
payload remains untouched. Its inert old loopback-export configuration was
snapshotted/fsynced before the reviewed offline export replacement; no existing
NFS client/server workload was disconnected.

Clean fixture construction at `78945407f285ccdafa9d0baf1effa99a8c139bcb` passes
the existing builder with reproduced backend/UI bytes. The bundle index is
`18b121bfae576ca3efaccaf16a7df957cc3037f7433bfb66e29807c5639a5356`, UI
`a7f508b63b9a8374e6020d473a64649d0deb7bc5d4817ded9c6f10508dd0726a`.
The independently streamed guest copy passes physical `verify-native`. The first
offline build's missing cached Ruff wheel remains a failure; cloning the existing
locked installed development closure supplies the prerequisite without downloads.
Only the new worktree's editable project path is rebound. These are fixture
artifacts, not REL-018 release or installed workflow acceptance.

The fresh guest has DMI `c534a30d-e0ba-4c6b-9f33-e939df3c6fa5`, boot
`150917c0-b7e0-45a6-a412-a87200c49ccd`, host QEMU PID2879642/start61325968,
restricted loopback SSH46326 and1536MiB/two CPUs. Its immutable backing was freshly
hashed/stat-pinned and all consumers independently proved read-only. Existing
guests remain untouched. Root reviewed the exact launch/cold-preparation steps.
The copied fixed service account is983:983; container UID981 must still be proved
through its actual keep-id mapping rather than substituted for the host identity.

Cold preparation preserves25 copied prefix/store/configuration/credential/link
objects by inode-preserving rename and records both original/new store locks.
Legacy writers/calendars remain masked. Preserved fixture failures include the
boot-time SSH timeout, `exportfs` adding explicit `secure` after nfsd mounting
without changing etab bytes/inode, and the new empty directory's umask-filtered
mode. The narrowly reviewed correction changes only that owned empty directory
from0700 to its intended0750. No assertion or product contract is weakened.

The original new-fixture application creation times out after90seconds during
the fresh NFS server's90-second grace period. Its original processes subsequently
exit; independent read-only application inspection of that same UUID reports
`initialized`, no problems and a present sentinel. The timed-out command remains
a failure; creation is never replayed. Kernel lease/grace, SELinux booleans and
hardening remain unchanged. Both stock `virt_use_nfs` and NFS-export booleans are
already enabled in this guest; no sole-systemwide-writer or strict-neverallow
claim follows. Direct installed product/security qualification remains pending.

Native fresh staging passes using the official installer and locked cached
closure: candidate0.3.1/index18b121…5356, copied Python3.14.6 with inspected optional
installers omitted, actual service-UID983 read/execute, unchanged NFS/global/store
inodes and no selected current or role startup. Fresh native `--no-switch` does
not enter the switch/rebuild flock guard: the caller's FD pins metadata only.
The original stage-before record's sole-holder wording is an intended guard
description, not an observed live flock claim. Selection remains a separate
guarded operation.

The real official switch then refuses the required masked/inactive
`hfcache-sync.timer`, preserving `current` absence and all masks/locks/mounts.
This is a product defect, distinct from the preserved fixture-only failures.
The small source repair recognizes only explained masked/inactive units and
retains the existing process/task/cgroup and original-flock guards. The one
strict source gate must pass before a clean detached fixture-source commit and
new immutable bundle are built. The never-selected stage1 candidate remains
preserved; no in-place artifact patch or unmask bypass qualifies acceptance.

Focused source regression passes29 cases/105 deselected, including deliberate
masked timer/service inactivity, preserved masks/original flock, active masked
units, leftover processes and unexplained task/cgroup/load evidence. Bash syntax,
Ruff and216-document/29-helper alignment checks pass. These focused checks do not
qualify the fixed installed switch; the original real failure remains retained.

## Completion evidence

The first strict source gate `scripts/check.sh --require-web` passes in1848.98s:
9727 backend tests/52 deselected, package build and three locked installed wheel
profiles,3809 web unit/4169 combined tests,16 built-browser checks, actual200%
Library zoom and real HTTP/API React reads at both prefixes. All1281 frozen
source names/hashes remain unchanged. The root-owned namespace wrapper supplies
an empty read-only NAS shadow and drops to loginUID1000/nice10 before execution.
The optional instrumented functional runner is not invoked.

Evidence is retained under `/var/tmp/web033-validation`: inner result SHA256
`6707e98792a97ce393bd932d4452a241d2fbd7b21e7b326c09382b4f9bf73ab2`, inner
log `f2b46f61852a2143a056123c838662afc56faef3ad4f37cebd22b82395c7c5eb` and
shadow result `be565cfaaf084f5215c44bef5ee49af9d614c277f04b88d8f4aa4a03da8750b1`.
The exact gated in-progress task bytes are preserved before this evidence-only
append. A clean detached fixture-source commit may contain this gated technical
change plus focused-checked task evidence; it does not complete this package or
advance the main selector. Installed acceptance remains pending. No passing
source, source-browser or synthetic fixture result substitutes for that work.

The gated technical bytes are subsequently captured in detached fixture-source
commit `145fa9f184ef1c44f385221ae15d91cdb7e5cd5e` (tree
`fee36c10c6c29e964b580238bafeb0c9452ddac5`), outside main. Its clean offline
bundle has index `25c7536ca3c9ebb7629050443c1bc3dffb294c21a87cca2e9f348b0fd2dc6912`
and UI manifest `d32ec727afc4648e4a252d55c6fc2bc5e7be6e94158890b31ae898bb11531c49`.
The source1 candidate is never selected and is preserved whole by nonreplacing
rename, with full inode/metadata/content joins and an explicit absolute-venv-path
limitation. Source2 fresh staging holds the actual original exclusive
`27:1938` flock; the official fixed switch then succeeds with all four original
masked units retained. That installed result closes only the reproduced masked
quiescence defect. Both NFS aliases and original store/global inodes remain
unchanged; no executor is started by staging or selection.

Owned-guest protected bootstrap then passes with selected source2 files and the
actual loaded CIL `0a5e65541c070d9e4affb08be2c25de072d994523214c01ffb5bd7c0df7b31c1`.
Old bootstrap/module CIL, kernel policy bytes, receipt and fcontext inventory
are retained before replacement. The same original exclusive flock protects
this metadata-only step. Its existing persistent rule assigns the original
global lock the archive-lock SID without replacing its inode or changing its
bytes/mode/owner. A separately measured receipt and deployment index
`55ce592badaf5324f2281129fca49d5c7ec9e7aba47d34b016104319dca9bd20` bind the
new helper; all six permissions remain false. The selected installed
`IntentInterlock` refuses the actual absent companion with `HFAPI015`, and both
stores remain only their original `.lock`. This is an installed admission-guard
negative, not an HTTP startup result. Canonical newly selected API-backed
scheduled observers replace the preserved mask symlinks solely in this owned
native fixture; calendars remain disabled/inactive and production masks remain
untouched. Offline transient/companion, helper READY, actual API/worker/Caddy,
browser recovery and rootless writer/security acceptance remain pending.

Full outer captures are `/var/tmp/web-033-fixture/native-stage2.json` (SHA256
`56c9ece88e022d4941fbb9f8d8523ff8ecdb36a525e32b1fce91263fb43cf1c4`),
`native-switch2.json` (`5e15d42bdcc6a556b014ea188caae18eaa993e057a665be40bf577134b6072ca`)
and `native-bootstrap1.json`
(`185c69f3bc78c2edcd605b0c0862190363cddaa9af5090fb3b8bb47ad508ce4e`).
The first bootstrap transfer's SSH shell-quoting refusal is separately retained;
it runs no guest Python. The corrected exclusive transfer and original reviewed
bootstrap complete once. SELinux remains Enforcing with unchanged booleans.

The actual official offline preparation then refuses before creating a transient,
backup or companion: systemd257 prints both structured credential properties as
`[unprintable]`, although the fixed system-bus arrays prove no plaintext loads
and exactly the canonical encrypted writer pair. This second product defect is
recorded before its minimal source repair. `busctl` and `systemctl` belong to the
same existing systemd RPM; no package or credential source is added. The repaired
parser requires exact typed arrays, rejects duplicate keys, unknown fields and
unexpected entries, and preserves bounded execution, canonical startup/imports,
API no-dropin, source masks and the before/after revision.

A separately named candidate module is then loaded outside the installed SDK
using its actual installed Python/dependencies, calling only the read-only
`native_mask_policy`. Its first run identifies a fixture-rendering error: the
bootstrap's temporary variable overwrote the earlier validated server TOML with
a path string. That original invalid49-byte leaf and failed probe are preserved.
Only this new owned configuration leaf is corrected from its retained template,
with strict selected-model validation and actual original exclusive flock.
The same candidate's second read-only metadata probe passes all actual native
predicates. The same function also passes under actual UID/GID983 without PAM,
with the identical revision, proving that identity can read the required system
metadata. These are not installed repaired activation evidence. The source2 SDK
remains unchanged and all roles remain inactive. The original bootstrap success
therefore proves protected copies/CIL/index/lock joins, not valid server rendering.

Focused native regression passes28 cases/30 deselected, with Ruff format/lint,
Pyrefly and216-document/29-helper checks green. Focused log SHA256 is
`a7c920178516e5f1e1fbe0268c18ee8968b6cdb3c80734c3fd3ec71d8d6a911a`;
candidate metadata preflight2 is
`9af23ced03a457bf3a7aa75912ff320cbc0b5f131df7927c963968ffc8d649ba`.
Final technical inputs require another strict gate and a new immutable candidate
before the original official offline preparation can qualify this repair.

Before the second strict gate, the coordinator restores the original1.1GB-root/
50MB-home launch floor through verified full preservation of two completed
ignored build-provider `.venv` trees, three completed private policy copies and
lossless encoding of known redundant manifest sidecars. Committed worktrees,
node_modules, bundles, refs, logs, failures, guests and production remain intact.
The two-provider archive is55,274,414 bytes, SHA256
`113f7b1f33a675690908a700407b7da8379e5907e55a186c0161170f836c3af4`;
its retirement receipt is
`81b50c3e7e2b145eeb818ead80afd01e480a20ef0f2f3fe993bb3b9e730451dd`.
Full content/metadata verification, fresh all-UID zero-owner proofs and durable
receipts precede exact named source retirement. The eleven-sidecar preservation
index is `/var/tmp/web033-sidecar-preservation-index.json`, SHA256
`95f78d978446ae392bcf7b51d16bfd40e3541008b174eee78613c02abfbf6cfe`.
Actual reported free space is1,137,815,552 root bytes and approximately62MB home;
the unchanged gate wrapper checks fresh floors before execution.


2026-11-04 reconciliation: the second strict gate is interrupted, with no
result files or pytest summary. Its log stops at90% in
`test_web_basic_sockets.py`; every previously recorded gate process and the
owned guest process are absent. The cause remains unproven. All1281 frozen
source names/hashes still match its start record before this evidence append.
Retain the entire `/var/tmp/.g33b` tree (device64768/inode751929, UID1000,0700),
start record, inner log and shadow log; no partial run is a pass. No guest
relaunch or production effect follows. Fresh free capacity is32,214,642,688 root
bytes and73,700,855,808 home bytes, so no further retirement is needed. The
original strict wrapper will run gate3 in new `.g33c` with its unchanged
1.1GB-root/50MB-home floors, private empty read-only NAS shadow, loginUID1000
and nice10. Final technical inputs stay frozen for that complete run.


The third strict source gate finishes normally on2026-11-04 with exit0 in
1473.558s:9741 backend tests/52 deselected, package build and all three locked
installed wheel profiles,3809 web unit/4169 combined tests,16 built-browser
checks, actual200% Library zoom and real HTTP/API React reads at both prefixes.
All1281 source names/hashes remain frozen unchanged. Inner result SHA256 is
`f9cfcf59a880da3c485aea2d358276e37ab10553789ddbd2d45d01872aee28d0`,
inner log `9529e84d3912358a04150eec3f4c9f8b3832d63ae2519de1444dab9fa9549dd4`
and shadow result
`35937bdfccf3d6d3ee3f7a01ba0109d3484171350b33a80318bfca5460cd5921`.
The exact gated task bytes are retained as `gated-task-record3.txt` beside those
logs. This qualifies the final technical source repair, not installed activation.

Independent read-only reconciliation identifies an externally changed host boot
`45d3ce1d735b45ccb731e2f39860d65f`. The production runtime archive lock is absent,
helper/API inactive and worker failed; production readiness is unproved. The
protected persistent configuration/stores retain their previous content and
inode/metadata identities, NFS remains read-only and SELinux Enforcing. Receipt
`production-postboot-readonly1.json` SHA256
`d40c260efca910e94dc63f8b3c8b856f971307dca8a8e12436ef1094f354651c`
records this current-boot prerequisite for OPS-028. No production restoration or
replay is part of this source qualification. Historical runtime inodes cannot
be claimed continuous across a boot. No host reboot was initiated by this work.

Before restarting only the stopped owned fixture, root preserves its complete
overlay as `guest-before-resume1.qcow2`, exact byte SHA256
`74a5abd22a43b1b89c3af48059219c06ff5340c4c384fe7994a0d1efe717db7a`,
with unchanged original and backing. Fresh all-UID no-owner proofs and copy-only
nonrepairing `qemu-img check` accompany preservation receipt
`b6c8bb487f3695d64b3adb32033ef07fa8382987ed1542194297073cfe9b4068`.
QEMU's forwarded SIGTERM and clean image-header flags do not prove guest OS
shutdown or journal completion. Root's reviewed owned-guest restart establishes
new guest boot `f6ec5b1d-a7f4-458b-8b00-bab0f9ef13db`, same DMI/service UID983
and Enforcing state; read-only inventory SHA256
`818a0a987a94003c061ec8cfde7089bad0c6dd7f8885d116c2e396f711fcf6d9`
finds selected source2 and inactive roles, with no NFS mounts or runtime global
lock. New current-boot NFS-ro/runtime provisioning and persistent identity joins
require separate protected review before source3 staging. Old boot/runtime pins
remain historical evidence only; no unattended-boot acceptance is inferred.


Detached fixture-source3 captures the exact final gated technical bytes at
`6fd83000cbf225e35d798995bc7abdf53b642d7d`, tree
`0d36af08ddaa46c8636c58168d88c42930cd2935`. Only the in-progress task evidence
is appended after the freeze;69 focused documentation checks pass. Main remains
`7894540`, with no partial package completion or production release selection.
The official clean builder runs offline under the private NAS shadow as
loginUID1000/nice10 and passes in10.479s, reproducing backend and UI bytes.
Bundle `/var/tmp/hfcache-web033-artifacts3` has index
`d85a2a57d6475dd51b8192d01fe16015afd7c974e6638b7997173dbe0e7147f2`,
UI manifest `02c940830eaa2a9f8b42ed15570c3af64efcdb8ff093652414d74ef9e58b6f60`,
wheel `505323dc2125906147c98fa53bd6106595c948d3c714417ab43e5b485fe6577b`
and sdist `0e1c9a83611f7c58c899838a6ff6df6e344be9e2955e00ae5964dbfbbeed4107`.
The source3 build record retains the nine changed file hashes/modes, all builder
logs and original source snapshot. Development copies preserve full donor
content/metadata before and after building; main environment/root node dependencies
require cross-filesystem copies, while retained source2 web dependencies permit
COW. Only the new environment's editable project path is rebound before the
official locked sync. The source3 worktree remains clean. No installed repair
acceptance follows until fresh staging and the actual official offline preparation
complete under the separately reviewed current-boot fixture prerequisites.


The owned guest's separately reviewed current-boot manual restoration completes
without replaying initialization. Runtime authority SHA256
`42e543ecf8ed31e82c235003ee98893fb7107a046db8f16582e531a75817572c`
binds new boot `f6ec5b1d-a7f4-458b-8b00-bab0f9ef13db`, original current-boot
global lock27:1706,983:983/0600/zero bytes and its canonical archive-lock SID,
plus helper runtime parents27:1739/1740 with exact owner/mode/SID. A context-only
`restorecon -F` normalizes the newly created global lock's SELinux user while
preserving its inode/bytes/owner/mode/mtime under actual exclusive flock. Both
loopback-NFS aliases are read-only/nosuid/nodev/noexec on0:48; persistent store
lock identities remain unchanged, actual system/user roles inactive and all-UID
executor/libpod checks empty. The earlier inaccessible-cwd and partial runtime
label failures remain retained; only the reviewed narrow tail resumes afterward.

Actual selected source2 SDK `read_sentinel`, running as UID983 against that real
NFS-ro mount, verifies schema1/UUID `fc118f3e-2b23-43e9-bc7c-24795b155031`
with no problems. Reader receipt SHA256 is
`38b62962b0630fab40fa785f55788488f8e5216a60ae0aa467b7cf4981461a12`.
The earlier write-oriented `inspect_archive` predicate intentionally reports
HFMNT004 on read-only storage; the incorrect verification-function assertion
and traceback remain preserved, without inferring corruption or initializing
again. No writable remount, payload edit, job or production restoration occurs.
Source3 transfer/retention/stage/switch/minimal-bootstrap scripts are prepared
and reviewed separately before any such protected effects; preparation alone
is not installed acceptance.


Actual reviewed source3 transfer and native replacement now pass. The streamed
bundle verifies index `d85a2a57…147f2`. Source2's complete7006-entry tree and
original current symlink retain7007 inode identities through nonreplacing rename
into `/opt/hfcache-web033-source2-retained/{release,current}`; full metadata,
content and ownership inventories accompany receipt SHA256
`fe259dbcca4abdd49d32cac23f584c8a2b105387b3ddf497e2a077e3690bfd48`.
Its retained absolute-venv/relative-selector restoration limitation remains
explicit. The fresh official native stage passes in63.4s while the caller
retains the original current-boot exclusive flock; stage receipt SHA256 is
`371ef2b7782371c71c6d60584440e6005a0ace3df39d6948c1e33e73d57627d1`.
The separate official switch passes in0.3906s as sole flock holder, selecting
`releases/0.3.1`; receipt SHA256 is
`7e8f445ec6eacb82b5d51c4ecdf40b4872e7170e1c612a0f5df080d3c367de2a`.

Minimal protected bootstrap3 passes in6.23s, validating both strict server
models, retaining the three original protected leaves and publishing only the
changed UI/server/native index/policy metadata. New native deployment index is
`f6ef4547bb11034c4c33890b00ed6580934f6d23becda6bb487ac86f63472229`,
with all six grants false. Helper/library/CIL/receipt/kernel/HMAC bytes remain
unchanged; no module recompilation or fcontext-policy write occurs. Existing
physical-path fcontexts label the fresh unit leaves. Bootstrap receipt SHA256
is `8c383d7d860cd67d5f59cc76581841a429d5b64896d9a22106049a434d318110`.
Original current-boot global27:1706 and persistent store locks remain unchanged,
both NFS aliases read-only, roles inactive and companion/backups absent. These
actual installed replacement results do not yet qualify the repaired official
offline activation, transient isolation or browser/rootless writer behavior.
Production's separate current-boot readiness prerequisite remains unresolved.


Before authority effects, the actual newly selected source3 SDK's
`--native-masks-only` preflight passes with all standard and both fixture-alias
masks, revision `b2a4d33807021e075af1addf2bdb3bfc5760e2c1b2e9c908ef7332e3adc11367`.
Receipt SHA256 is
`501d276d4326bcb6309769844e297690147aae2111b9b86c76481b843fab90a4`.
This closes the original installed metadata-predicate refusal; actual transient
execution and companion publication remain separate uncompleted checks.


The third actual official offline attempt fails: exit1 after0.911s with
`Failed to start transient service unit: Remote peer disconnected`. Outer
receipt SHA256 is
`c0e0e5122d2f91f37d3d8109fd96f50b4004b2f86112f2893f4834c11839ba09`,
installer log `9d25db0b63a89e36b8f6449fa3270f5bbc85756a60797fc3e2e46ce1129a096a`.
No transient is captured; fresh inspection finds its unit absent, PID/control
PID zero and cgroup empty. The two newly created top-level directories are
empty: backup64515:103406351 and private runtime27:1905, both983:983/0700.
Disposition/private companion/published companion/initial manifest remain
absent; current global27:1706 is unchanged. Inspection receipt SHA256 is
`305d9818f73d1357b9e12d79d40e2c78a39e8ae95c76d9ad4af0f3e997abafcc`.
All failed logs, directories and observations remain preserved, without replay
or treating missing state alone as proof of historical nonexecution.

Journal diagnosis SHA256
`6c22e061bb15a303fb1b981e77080d809e6f03aa5a25805ba0d94ed200994939`
identifies an SELinux denial when PID1 receives the capture parent's private
admin-home log descriptor through official `systemd-run --pipe`. The narrow
capture correction supplies a pipe to the official CLI and lets only the
collector parent write the evidence log. No product source, SELinux allowance,
policy, label or hardening change is required by that correction. A separately
reviewed preservation step must first retain only those exact explained empty
directories by nonreplacing rename on their original filesystems. Neither
prepared capture4 nor preservation script is executed by task preparation.


The raw enforcing AVC confirms capture3's inherited-FD blocker: audit
`1793793267.855:901`, PID1 `init_t`, denied write to the private
`admin_home_t` installer log, `permissive=0`. Alert receipt SHA256 is
`95c97f750b393d785a2f017b69210f0367794c47c2f792ff2d662c3c0a814ce0`;
the earlier unmatched ausearch query remains retained. No suggested policy
grant is installed. The reviewed exact-empty preservation then passes, retaining
backup103406351 on its original persistent filesystem and private runtime1905
on its original tmpfs, with original locks and failed logs unchanged. Receipt
SHA256 is `8b75deb30212dfe433cff83cc1896fc747a9e4484e6c3f307fa17d79b2c6b583`.

Actual official offline activation4 succeeds with pipe-only child capture;
outer receipt SHA256 is
`a84b53f92fae9fc28046353480e4e1a35101cda60693b83cf3b80b5871beeb5d`.
One actual transient observation captures PID3060/start370575, UID/GID983, all
capability sets zero, NoNewPrivs1, `/dev/null` stdin, independent network/mount
namespaces and exact safe offline environment with no forbidden credential
variables. Fixed source/credential masks have actual private mount/000-mode
metadata, and private runtime27:1995 matches its source inode. The original
observed PID subsequently closes; terminal MainPID/ControlPID are zero with
absent unit/empty cgroup before the phase-specific worker mask is retained by
nonreplacing rename. Reload restores both canonical API/worker DropInPaths[].
Observation and terminal-closure SHA256 are respectively
`29db4cedd0a31c32280cb7e0d577bfdc438b6dcb2f5278a30530cabe610a65aa` and
`ef6c508e07dd1dd640caaed93f57b990b10b953c9f2d89f8c69b46e43fedb041`.
New companion27:2004 is983:983/0600/zero/nlink1 with the full canonical
archive-lock SID. Empty disposition1 has SHA256
`1d493aa1689df2a757be5a319a95c9d1cc1e594d0458de64658d8241bf797a94`;
coordinated backup manifest SHA256
`cd1d1b4c804e25d63c3dfcdb3310406261e59b4842db86668d631f3a17de4f6a`
retains both original empty store-lock hashes. Global1706, persistent store
locks, NFS-ro and Enforcing state remain. No helper/API/worker/Caddy is started.

Fresh read-only post-offline cohort receipt SHA256
`ebd599c8f3d358ce81436322d91d3cb511c5250f3f7444b98b7655a003b4c0f3`
pins exactly five inert UID983 infrastructure actors: systemd1162/start1587,
executor1170/1602, pause1513/70644 and broker1526/70669+1527/70671. All app
units remain inactive. The complete libpod inventory retains four historical
exited/Pid0 containers; active-only emptiness does not mean their removal.
Their engine indexes, linger25991610, runtime and persistent lock/authority
metadata are captured before preparing a separately reviewed graceful cohort
drain. The temporary non-killing dropin must be retained on its original tmpfs;
no cross-filesystem rename, forced termination, migration, linger change or
post-drain PAM is part of that procedure. Production's cold hold is unchanged.


Root independently reviews the actual native offline4 observation and terminal
closure, beyond its summary boolean, in receipt SHA256
`2893a1a76576cfcc85096d363cef19ade4bed24bc0e41b804c1b6e521c3a69ae`.
The actual native isolation proof remains separate from rootless qualification.
The current deployment checkpoint and Operator handoff now carry a small dated
production post-boot hold, retaining older readiness evidence and the selected
artifact source. These evidence-only updates leave current task selection intact;
scoped documentation checks remain required at the eventual package commit.


The reviewed fresh-cohort drain executes once and passes in1.798s; receipt
SHA256 is `47e399f63b4b132725acd1c24382ba02f7c9073844b978f1158caab58e2bf000`.
All five pinned inert infrastructure actors close, user@983 becomes inactive
with MainPID/ControlPID zero and empty cgroup, and all13 fixed authorities,
original global1706/companion2004/store locks, marker/backup, engine indexes,
secret identities and linger remain unchanged. The four historical exited
containers remain retained. The owned temporary non-killing dropin is retained
on the same tmpfs under `/run/web033-cohort-resume1-retained`, and original
manager properties are restored. No UID983 PAM/runuser/Podman follows this
drain before a separately reviewed rootless phase.

The actual native helper starts and reaches Notify READY: active/running
MainPID3582, ControlPID0, Resultsuccess. Receipt SHA256 is
`7ee3f26c0797ad7717801aaac1a8fa8266a3887be5e46286cff1120d09e57463`.
No API/worker/Caddy startup or browser behavior is inferred from helper READY.
Read-only startup-binding preflight SHA256
`6bc064146d0855a2da47e56ff44c73bf74b8f499c1d47343c0e84e8116cad5c9`
confirms the existing canonical API Unix listener/Caddy alias and configured
`/management` TCP root path, canonical private worker socket/peer ownership and
empty API/worker DropInPaths. No listener configuration change is needed.


Ordered actual native worker/API/Caddy startup follows helper READY and passes;
start receipt SHA256 is
`827de2d61b25eae05fbb0b68fc98ef4ff0ab03c61eb9540471faac0724c7f6af`,
settled actor/SID receipt
`5f2bd66edea10af2be6e7a8c07ede5fd8dd88366b454f535222f66b6664c753b`.
The UID983 user manager remains inactive. Browser prerequisite inspection
correctly finds both owned CA and leaf expired on November1; verified TLS is
not bypassed. The separately reviewed PKI renewal retains original public
certificate inodes and reuses the exact CA/TLS private keys, public keys, CSR
and extensions. Its initial final curl races proxy startup and remains a
failure; fresh read-only settlement proves the renewed chain/IP and expected
unauthenticated Basic401, with Caddy4251 active. Settlement receipt SHA256 is
`542e313e0c2873033dc397cb3af0cd160e97b14ae49aace410c66e1fd8f2e231`;
renewed public CA SHA256
`949c711c29051bf59a32f12d927ea44e092e7546b844fbddadda671e3fd7f986`.

Actual authenticated read-only preflight then passes six verified-TLS GETs:
bootstrap/version/jobs-readiness at root and `/management`, all200. It proves
Basic subject `web021-admin`, selected source3/UI identity, read-only archive,
denied Hub/archive/control grants and actual API-origin private worker PROBE.
Receipt SHA256 is
`3587fd921e68fa5d615c2030b4a845e19717d46b9d8271f60692f287b68d56b4`.
Only the owned `/root/web021-private/secrets.json` Basic donor is reused,
verified against the actual selected Argon2 administrator record in RAM. No
credential value/header/body is logged, and donor/verifier metadata and all
store bytes remain unchanged. No browser JavaScript or job runs in this probe.

A new private browser trust fixture preserves the cached image and all old
artifacts, combining the exact old183673-byte public system CA bundle with only
the renewed public CA, for a read-only bind at its canonical system path. Fresh
NSS/Firefox profiles use the same pinned renewed anchor. Actual trust preparation
receipt SHA256 is
`19305ffc1ca3601d24ada9f6b47480abed71c4839dd266b878aed71827b5c1d8`.
The finite direct three-engine/two-prefix availability/review driver and exact
all-false launcher are prepared for root review; no browser execution is inferred
from trust preparation or the read-only probes. Earlier bound/GraphDriver metadata
inspection failures remain retained.

The matching source3 application image independently builds offline under the
private NAS-ro shadow as loginUID1000 using the official cached-input builder:
`sha256:2cde462821f06e67a8c2195325b87de060b66025965b98e6275fd16b38aef26c`.
Build log SHA256 is
`1e0478d6eaf53080bbc895b0f6971128d8327f0312af37bdc4ced9c33998f9d6`.
Official final-image foundation proof SHA256
`f1e6460f304422de6ba34a2530cde33b35481ab54c1aff9a861bc5806203c4e8`
qualifies its pinned UBI10 micro lineage, isolated readonly/no-network/no-bind
UID981 imports/tool absence/cap0/NNP/seccomp boundaries, separately from installed
rootless host mapping. The66,336,768-byte OCI save SHA256 is
`46a6ad0b8ad7501f938f5afd1886fecb365ee58cabc1c19d953131b583438bbd`.
Fresh immutable Unix-only rootless input captures `/management` before manifest
construction, so the existing UI mechanism serves root/configured shells from
one profile. Pure official validation passes guarded manifest
`960615079958e90d72ee08c1457e87c061ad7cdf7db4fbca857c4348b1645e44` and
manual-writer manifest
`af50392335f238b711750c849bf800e31e1808ad87bddcadf0dd8fa528279c2f`,
receipt `3d5cd71a126a529b84536960b8a9b879384a0f1ebb909d0693a2442606ac3f56`.
Root-only transfer/preparation is not guest import, staging or installed rootless
acceptance. Production's separate cold hold and all publication boundaries stand.


The first direct availability/review browser phase fails once before its mutation
loop: Chromium root opens and pins the correct build, then the fresh Chromium
`/management` case times out waiting for the expected readiness response. The
original report retains two unfinished cases, closed contexts/browsers and empty
stderr; failure trace collection is incomplete because the original driver
assigned per-case request arrays only on success. No retirement seed or POST
has run. Outer failure receipt SHA256 is
`75d5f772df872a835e066c1ea380d2cc80128c50fbdd825eb79f2ade13522f28`.
The original driver/trust files, report, failed container and all artifacts
remain unchanged. A fresh read-only Chromium management-only diagnostic is
prepared for root review, with live paths/status traces, bounded UI/bootstrap/
readiness projections and memory/swap pressure; no all-six rerun, deadline
change, guest resize/restart, seed, job or retirement is inferred.

Independent failed-container closure receipt SHA256
`fdbf725508aa00eaaaf6ff467dfdcca71acc93a00307c94bd6f17410d6942106`
proves CID `4221e10f76039ef96c244a350a0936be7449c05445d0f6bb16332e626b853812`
exited1/PID0 with empty cgroups, unchanged fixed/private metadata and native
service PIDs, inactive UID983 manager and still-empty disposition state with
original SHA256 `1d493aa1689df2a757be5a319a95c9d1cc1e594d0458de64658d8241bf797a94`.
This is a named acceptance-harness investigation; no product source change or
new source gate is justified before the actual management path is observed.
Root-only OCI/sibling-input transfer receipt
`016b40556a8d5a0921e67cc6b850c52cab1ab8348cf581bcdfa8a394ca6a5a86`
still performs no rootless import, staging or UID983 PAM.


The single read-only Chromium management diagnostic completes with actual
closure and unchanged authority/state. Outer receipt SHA256 is
`109d30916c6dc4b23a576228a47b950b197ced153a707b0723c2db248ccdf26a`,
original guest report
`b75fe95ac3516c1e80f46e90286297aa7b0ce0c44b798fb6ca71c8a81db2cbef`.
Actual management shell/base/bootstrap/API paths are correct; both observed
readiness GETs return200, with no page errors, failed requests or external
requests. The UI changes from Checking to the correct Hub-disabled explanation.
Thus the failed original response waiter is not proof of a path/product defect.
The observer's10s waiter starts before navigation/bootstrap and is shorter than
the actual source client's30s default request boundary. No elapsed route timing
was captured in that first diagnostic. PSI collection was unavailable, not proof
of healthy pressure; independent guest metadata reports1492528kB total and
792444kB available RAM, no swap, and no memory PSI file.

A new availability-only attempt2 is prepared for root review, preserving the
failed original and successful diagnostic unchanged. It aligns API-dependent
waits to35s (existing30s boundary plus browser delivery), persists live
method/path/status/elapsed traces from case creation, and closes each prefix
context and engine before proceeding. It changes no product deadline, guest
resource, policy or source. No causal/lost-ack phase is part of that attempt;
root must review and execute it before any new installed acceptance is claimed.


Root's partial installed predecessor-format drill runs the exact `c23abba` wheel
from an isolated retained site, with the93 locked dependency versions matching
the selected runtime. Against an exact copy of the activated empty control
store, actual old list/expire/lookup/admit each refuse with HFAPI014 and leave
the copy unchanged. Receipt SHA256 is
`e972c163accb245a037f9f2dd491486b1674196dc8aa6a2a3029da35f73f0574`.
The missing-uv-PATH setup failure and incorrect error accessor after an actual
old-reader refusal remain preserved; the completed installation is reused.
Actual terminal-receipt/nonempty-fence, old-browser and profile rollback drills
remain pending, so this bounded result does not close the format matrix row.

Before the prepared availability attempt2 is copied or launched, source review
finds and corrects one further observer race: changing the job kind deliberately
clears advisory readiness while a fresh GET runs. The observer now arms that
GET before selecting Installed sizing, requires200/Hubfalse, and waits for the
actual Hub-disabled explanation before asserting Submit disabled. This preserves
the supported explicit-submit-while-Checking behavior and changes no product
logic. Both source-backed observer corrections remain separate from installed
behavior acceptance; original failed artifacts and technical source stay intact.


Availability attempt2 reaches the first actual explicit retirement POST and
fails503. Chromium root proves the archive-disabled explanation and three
readiness200 responses, then schema1 migration and original-key intent GET200.
The sole POST `/api/v1/operations/intent/retire` starts at18577ms and returns503
at22784ms; the observer subsequently times out waiting for retired state. Outer
receipt SHA256 is
`99ac3b3721e8a343034a63d29de1db493350078da1212679908ceae49b90dcac`.
All original traces/report/container evidence remain. The harness did not
durably export its newly seeded nonsecret record/key before the effect; later
observers must do so and retain a bounded typed problem-code projection on the
original failure response. The POST is not repeated to recover that body or key.
No production handle or browser record is touched by this owned-fixture failure.

Actual read-only journal/closure diagnosis SHA256
`e381d4af369f272939f91bd7dcaecf14e92d94a58fb03a33852813e7abf64eb7`
finds helper3582's PermissionError/errno13 in `review_intent_locks` line2753,
through `capture.parent` line431. This occurs before the subsequent masked-unit
predicate. The browser container is exited1/PID0 with empty cgroups; current
disposition remains empty with original SHA256 `1d493aa1689df2a757be5a319a95c9d1cc1e594d0458de64658d8241bf797a94`,
no admitted receipt exists, and original global1706/companion2004/store locks
and native service PIDs remain unchanged with UID983 manager inactive. Missing
state alone is not promoted to historical nonexecution or permission to replay.

Exact runtime/helper metadata receipt SHA256
`281be820ea78a26ce0c8cb096254a2ad73dc54128bc0b5039d68f40a895aff7d`
proves `/run/hfcache`27:1329 is983:983/0700/var_run_t, while confined helper3582
(start484714) has UID/GID0, supplementary983 and effective/permitted/bounding
capabilities0xc0 (SETGID/SETUID only), NNP1. Its direct read-directory traversal
lacks the required DAC access. Native service/socket contracts deliberately
retain0700; no chmod, DAC capability, SELinux allowance or threaded-process
credential change is an accepted workaround. Existing separate metadata-child
identity machinery is the bounded repair direction to review. The finite matrix
adds this row solely for the actual reproduced installed defect.

A distinct possible next prerequisite remains explicit: actual sync/verify
service units are inactive/zero-PID/empty-cgroup but linked and unmasked after
the earlier owned bootstrap restored canonical API-backed observers. The helper
intent-review predicate requires inactive/failed units and masked service units;
timer names separately permit inactive unmasked state. That later predicate is
not claimed as the cause of this observed earlier DAC exception, and no mask
or link change is performed here.

The coordinator escalates this named security/runtime repair from the task's
medium effort to a fresh `gpt-6.1-sol`/high task agent under the active plan rule.
The medium agent stops phase preparation after this evidence handoff, with no
product source edit, fixture effect, POST replay or new gate. Root's separate
thread-flock proof rules out the suspected PID/TID mismatch (actual TGID6404/
TID6405, proc flock owner6404); its owned empty proof lock and receipt remain
retained. The scoped actual repair and installed conformance are still pending.

2026-11-04 bounded coordination-metadata source repair: the explicitly selected
fresh `gpt-6.1-sol`/high agent implements one fixed internal
`observe-intent-locks` branch over the existing bounded guard-child launch. It
shares closed bootstrap/budget/deployment/account validation but never invokes
the active-guard predicate. Only the separate child clears groups and uses the
existing mixed effective service IDs. It checks both original fixed lock inodes'
ordinary0600/service-owner/single-link metadata and exact coordination contexts,
brackets them with captured-authority/metadata revalidation, and opens neither
body or flock. The parent stays at its threaded credentials, validates the
closed typed reply and charged work against its deployment, reads actual
`/proc/locks` for the authenticated API PID's exclusive companion flock, and
pins complete metadata/contexts plus runtime-parent identity across review.
This also removes the latent generic `capture.label` root-owner assumption for
the service-owned companion. No permission, capability, label, unit predicate,
public helper opcode, dependency or archive authority changes.

Reviewed INV-020/023 and ADR141/150/159/164/165 against the narrow repair;
ADR164, INV023 and the host/recovery contracts now state this metadata-child
boundary. Existing guard behavior and actual-exit timeout drainage remain
covered. New focused tests reject malformed reply/accounting/identity/context,
unsafe/missing/replaced companions, changed parent/full metadata and absent,
shared or wrong-owner flocks. They prohibit parent credential changes/runtime
traversal and both child lock-body opens. An actual owned multiple-ID USER
namespace test runs (no skip) with SETUID+SETGID-only effective/permitted/bounding
capabilities and NNP1: root's direct traversal of the service-owned0700 directory
raises PermissionError, while the mixed-ID metadata child succeeds and the
parent credentials stay unchanged. It models SELinux context bytes explicitly;
this is DAC/capability evidence, not installed Enforcing conformance.

Focused command
`uv run --locked --extra server --extra mcp pytest tests/unit/test_host_intent_locks.py tests/unit/test_host_guard.py tests/unit/test_host_daemon_startup.py tests/unit/test_intent_review.py tests/unit/test_host_policy.py tests/unit/test_host_daemon.py -q`
passes450 tests in26.87s. The final refinement to restrict bounding capabilities
and set NNP in the actual USER-namespace test passes its exact targeted rerun
(1 test in1.15s). Changed-file Ruff lint and format checks pass; project
`pyrefly check` reports0 errors; `git diff --check` passes. The initial focused
run caught and corrected an eager observer-dispatch lookup in the new source,
and the later companion-replacement negative test caught its own mutation being
blocked by the intended no-body-open assertion; the test now uses a precreated
replacement inode. These failed runs remain distinguishable from final passes.
Source repair does not reuse gate3 as proof: the coordinator owns one new strict
gate after technical freeze, clean immutable construction/selection and the
actual installed retirement. No fixture/prod effect, POST replay or commit was
performed by this source agent; the conservative masked-unit prerequisite stays
unchanged and remains separately owned by the coordinator.


Strict gate4 passes after the bounded metadata-child repair, in1465.94s with
all1282 frozen source names/hashes unchanged. Backend pytest reports its normal
terminal summary:9772 passed/52 deselected in1155.96s. Package build, all three
locked wheel installation profiles,179 generated wire definitions,3809 web unit
checks/4169 combined checks,16 built-browser checks, actual200% zoom and the real
HTTP/API React read fixture pass. Required sandbox/functional metadata stages
report23/19 passing with no skips. No optional instrumented functional runner is
invoked; this remains source evidence rather than installed acceptance.

Result/log/shadow-result SHA256 are respectively
`f7479cfb180f6a13a3a267fc45a39ddf1df6eba33e59a0bfe0457bd4f37a6c31`,
`550079cb1eddee96f53106d81198a470ea5e8b27133a675d6e609a11b8c7b837` and
`cfc2802cbee0b24f0c5e2379bb5486be56ce2313fd107f57880730085df1806a`.
The exact gated task bytes are retained as `gated-task-record4.txt`, SHA256
`5fce00d2ebfc225cd5b84632ceb00f253118dbe87c1ab4cd57317c3f87dc0df9`.
The existing private NAS shadow/login-UID1000/nice10 wrapper is reused. Full
interrupted gate2 and all prior failures remain preserved. Only factual task and
selector evidence changes follow this green gate; scoped documentation checks
precede the clean detached fixture-source cut. Main stays at its completed
work-package boundary; retirement under Enforcing, rootless writer/format/browser
qualification and the later production work remain pending.


The passing gate4 technical bytes and scoped-checked evidence are captured in
clean detached fixture source `33efee6b204f202b96237536522a8c513973b2e9`, tree
`9d23e2f61004c635a4eb9cfeb0f6c995db84540c`; main remains7894540. The69 scoped
documentation checks pass after the factual task/selector updates. Existing
source3 tool donors are copied on the same filesystem and remain unchanged
through the builder; only the new environment editable path is rebound.
The official private-NAS-shadow/login-user builder passes in10.225s and
reproduces backend/UI bytes. Index/UI/wheel/sdist SHA256 are respectively
`2527a7796232dab8b57e587078651ae119b780a89bdc8f7036f386da92bbcae1`,
`4823909ba2fadb325e0fc43e3c7aaeea06f5a2c7f48456d570ca40d6e5b86fbe`,
`e82e30c9a264d20a47a1c274a8fb106efb4ab2d00a2e90974a2e2e27a065b822` and
`b6ebfaaa521dd35e65069ecd5240bf6f556969fbad82c4ee2003107b24f0f307`.
Snapshot209f9b8697dbca15f562d692f3a973c0434e5d280fff7c6b2677a28c165c2d9c
binds the genuine build receipt. Guest transfer and physical verify-native pass.
The matching app image is
`ebdcb7b1d8b3b0e19ea61dec75579af47665baf4d232e2698ff434ea9a318e19`;
its actual NAS-free/no-bind/no-network foundation proof passes, SHA256
`f58d6868d6a86b3b2b7992d68b3e50ecaa0ab4df7e5f3887490a0699ebd09fc0`.
It is not imported into the service account or published.

Fresh pre-upgrade snapshot outer SHA256
`fb33311a971f6233c6f93246e87001d29ab132ff3f3b381df14e14497b38b89a`
pins the live native actors, original locks/stores, credentials and permissions.
The protected coordinated backup and graceful proxy/API/worker/helper drain pass
in3.253s; outer/result SHA256
`dd9683a00f893abcdf93c5eeef40108fa5be24f4fca5d9c5203804fe882fcd00` and
`9c3229657c7a103fd993d4b14da0d79dfa6fa5587068f16d132a057362e14ce6`.
All original process/task/cgroup and UID983 actors close before original EX proof.
Global27:1706, companion27:2004, both store locks, marker1d493 and activation
manifestcd1d remain unchanged. Caddy nonkilling dropin is retained on its same
tmpfs; original hardening is restored. The whole selected source3 release and
original selector are retained by nonreplacing rename,7006entries/7007inodes,
with all bytes/modes/owners/mtimes/xattrs/inodes intact; receipt SHA256
`0c58d68de6ab93552df3456a21d338dca49ce1b23653e0f3a7a4ce478079bb5d`.
Both original physical paths and matching authority must be restored under drain
before using that retained absolute-venv/relative-selector predecessor.

The first stage4 precondition stops before candidate/work creation because the
user bus is deliberately drained. The failure is retained. Read-only proof shows
all application roles closed and no user/global application autostart links;
root explicitly starts only the offline user-manager infrastructure. The unchanged
reviewed official stage then passes52.383s under original EX; receipt SHA256
`0670c51ce148296ec39df6d63d6e21de4b784279207b088c544ba23d44fc484a`.
Official switch4 passes0.456s as sole original-lock acquirer, preserving all four
observed inactive/disabled canonical unit links; receipt SHA256
`dac8f764fb0ef9d6c0f16b211f428dbb7d101f5306af46d367e56c637c1e29bb`.
Source4 is selected but no helper/API/worker starts. Existing published companion,
disposition and activation backup remain; first activation is never repeated.

A separately retained prerequisite remains explicit: optional host-action guard
and record root are absent, but eight inherited backup directories remain. Their
exact root inode102286488 and UUIDs already appear in prior cold-fixture evidence;
they predate this new fc118 archive generation. Root preserves them unqualified,
without deleting evidence or inferring historical nonexecution. Any separation is
explicit new-owned-fixture provisioning under actual drain/original EX, never a
production/foreign-key recovery or generic retirement repair. Existing config
history9a80 has a valid original-key signature and confirmed phase for older
archive1c27a222-f3c5-449d-a4da-806fd293d974; administrative signature classification
is not complete helper authority. The direct SDK authority check correctly refuses
an unconfined operator context, and no domain bypass is attempted. Full installed
Enforcing history/retirement proof, preserving masks and a fresh offline-infra
drain, remain required after protected bootstrap. No production state changes.

Protected source4 helper replacement and bootstrap now pass in the owned fixture.
Receipts `native-helper-replacement4.json` and `native-bootstrap4.json` have SHA256
`ac47ca4b4fd313667ae8f800ac5093d1b3f17e8ed0a200ced8dece0f0105940f` and
`38adeaf42c0d93b6d700e4dd8b5a25445c71b7814425df435c124cf99840a89a`.
Old helper/server/index/policy objects remain retained by inode-preserving rename.
The new protected deployment is e8c816197ee457b8c43526ad6291ad810e7fd64e3b1602e0e6f265027303f6db;
policy inode61427500 retains all six grants false. No app role has started.
CIL, kernel policy, booleans, hardening, credential identities, original global
and companion locks, stores, disposition marker and initial activation backup
remain unchanged. Optional inherited host-action history remains unqualified.

The first final-infrastructure snapshot fails before mutation because Podman
inherits the SSH user's inaccessible working directory. Its failure is retained.
The corrected read-only snapshot uses cwd=/ and passes, pinning exactly five
UID983 infrastructure actors, all app roles stopped and four original exited
containers. Rootless source4 guarded/manual captured manifests validate through
the official parser (33 files), and the matching app image is saved/transferred
to the root-private fixture path without import or activation. OCI archive SHA256
is9e271f54e0b213242c8b4c5ef6c5b45052bf0d12ee23c91346f9fe95542f8325,
66344448bytes. Both profile inputs transfer with exact file hashes. No publication,
production mutation or installed writer acceptance follows from these steps.

The final source4 inert infrastructure drain passes1.917s; receipt SHA256
f3b475b553eceeebfe34e01f81b396a89331b82c96d3cf9fea6c5968185be9f0.
All original UID983 process/task/cgroup identities close, manager hardening is
restored and the new nonkilling override is retained whole on its original
run tmpfs. Fixed authority/helper/store/engine bytes and secret identity metadata,
linger, original locks and both RO mount rows remain unchanged; no postdrain PAM.

The fixture four-mask restoration then passes with original canonical links
retained whole (receiptfe523f5e0c9bae2f9c1df55dfcad77b586def44fb4afe067896521a9cce4935d).
A subsequent grounded review identifies a conflict with the helper's canonical
native binding link check: the /etc links cannot also target /dev/null. Before
any helper/application start or recovery POST, root restores the exact original
canonical link inodes by nonreplacing rename, retaining every new mask link too.
Restoration receipt8a245a254ace2354df259aa6b563c2e320fa88c92aa22b629b5c42c5b56dbc46
passes with all roles/UID983 closed, original EX, grants/mounts/locks unchanged,
and calendars disabled. A supported separate higher-priority mask must be
qualified before online acceptance; neither predicate is bypassed or weakened.
This temporary fixture sequence never changes production masks or starts a job.

The separate runtime-control masking path now passes actual installed checks,
receiptadb0b2aa941f3054ddda14f4643ae7a597ac27fa9f54eb6ccbe292648f38c1ef.
Guest systemd257 orders `/run/systemd/system.control` ahead of the canonical
`/etc/systemd/system` links. Each of the four new fixed masks reports
LoadState=masked, UnitFileState=masked-runtime and ActiveState=inactive. All four
original canonical link inodes/targets/modes/owners/mtimes/xattrs remain exact;
all application and service-account actors stay closed, original EX and both
store/companion locks remain exact, and policy/mounts remain allfalse/RO. This
satisfies the separate manager-mask and protected binding predicates without
source relaxation. It is explicitly current-boot fixture proof; no production
mask or unattended-boot acceptance is inferred. The next browser observer is
source4-pinned, syntax-checked and transferred as a new private file. It exports
nonsecret original handles durably before each deliberate retirement POST;
original responses are observed once and any refusal is retained without replay.

The reviewed fixture-only inherited-history separation passes; outer/result
SHA2567cc060d3ee35c70b090b39a9320bf89aa2fb46c676185fb10e1d2c8d97a4db2f /
48aecd0385e06130dadd29ea55f2d57439c3707afd6c897d8a2f29a6fc8a1728.
All13 inherited nodes, four predecessor bytes and rootinode102286488 remain
whole/inode-exact under `/root/web033-native-source4-action-authority/inherited-schedule-history`.
Old outcomes remain unknown. Only new empty fixed history directories and the
previously absent guard are exclusively provisioned with the existing loaded
types; no parent/evidence relabel, fcontext, CIL, receipt, kernel policy, boolean,
permission, archive access or authenticated old-record invention occurs. Existing
foreign confirmed config history, original HMAC/credentials/stores/locks and new
fc118 generation/allfalse scope remain exact. This is not a production recovery
procedure or evidence that old host effects never ran.

Ordered startup1 reaches helper READY and starts the worker. Its immediate
Type=simple observation catches the worker before systemd finishes setting NNP;
original failure remains dea607060837bbd8f950a796665b028fc514cdcc80d54a465db8cfcfdca8cd4f.
Fresh read-only settlement shows the same helper9244/worker9261 confined as
expected. Finisher starts only the remaining API/Caddy once, with bounded
same-process sandbox settlement and zero restarts/replayed starts; receipt
5e2d94cd0cd087eadb7dd43b8f0081a73c6a853587c482282c33375f911f2cec
passes. Actual helper SID/capc0/NNP1 and app/proxy UID/zero-caps/NNP1 are captured.
Six actual direct local/no-proxy/no-redirect/verified-TLS Basic GETs pass both
prefixes, exact source4/UI and API-origin worker readiness, with stores and
credential identities unchanged; receipt
2c2cafef09cf7af05631924d9d87c9cf465bc0b86a36a3b112a330b0b073ec5a.
Known fixture donor matches selected Argon2 verifier in RAM; no secret in argv,
environment, logs or outputs. No production authentication is inferred.

Availability3 correctly renders accessible Sync/Hub unavailability and migrates
an uncertain schema1 record. It exports original record
013bbc5215bf48c0a5cd80f954ad6852 / keyc943a22c-2c52-4da1-b938-8bed60842899
before effect, then observes exactly one original retirement POST503/HFAPI015.
Report3f54eb6b740fd68c98a7a4ddaa89b7e5b0f6192ca35e54d8a0e047de38715077
and outerb189f91a0cb73ef354f0b19186d2aa1ab1500a9a8f9d8e20c86b64c466574a1e
are retained, with original handle and historical uncertainty. No POST is
replayed to obtain a clean response. The source4 metadata-child check advances;
actual helper diagnostics now identify a separate later whole-executor scan
failure: host_peer._intent_executors line2405 -> _read line192, PermissionError.
Actual audit4743 denies helper_t read of the kernel_t `/proc/2` directory while
UID membership is being classified. Python ioctl/cert-import denials elsewhere
in the same bounded audit slice are not promoted to the causal error. Neither
unknown processes nor permission errors may be ignored to pass review. This
named unresolved security defect gets focused high-effort review; no ad-hoc
SELinux/permission/capability or retirement-predicate weakening is applied.

Independent actual browser closure/no-effect proof passes, SHA256
f532de68d4571a51cda5d8efcb57defe16a919c696971e9fe3442a67e9bb5a61:
container2b707fc4 exits1/PID0, browser cgroups empty, contexts/browsers closed,
original fixed/private metadata, native PIDs and mount rows exact; disposition
marker1d493 remains zero entries and neither operation store admits a receipt.
No archive job/write/grant change or production effect occurs.

Focused high-effort repair now freezes for strict gate5. Contract-first ADR150/164,
INV020/023 and host/security/recovery amendments state the necessary whole-host
proc-state boundary and its type-wide limit. The fixed peer reader changes only
ancestor handles to no-follow O_PATH; leaf reads retain their existing bounds,
protected ownership and no-follow checks. CIL adds domain-directory getattr/search
and domain-file getattr/open/read, without directory listing/open/read, symlink,
process, control, write, capability, namespace or transition permissions. Other
proc files such as environ share process labels; DAC/proc read gates remain
independent, and attachment denial is not universal environment secrecy. Fixed
code returns no foreign contents and strictly parses exactly four UIDs, retaining
coherent UID/birth observations through cgroup classification. No ownership,
kernel label, failed read or unknown process is skipped.

Root independently compares all38 complete existing neverallow forms to HEAD;
they remain identical. Distinct archive/NFS, Hub and credential/secret denials
remain mandatory; expanded-policy and actual Enforcing metadata/payload-denial
qualification are still pending. Source hashes host_peer/CIL are
ddd0ae0d9f323922c8809a71df0cb9a8fec65d5e6b6a0278c8b78eefdc4863c7 /
6b7585a202894fae629c5df18653a77cd2c9d678012f0ec3a31f592696caa8b2.
Focused command `uv run --locked --extra server --extra mcp pytest -q tests/unit/test_host_peer.py tests/unit/test_host_engine_runtime.py tests/unit/test_host_selinux_policy.py tests/unit/test_host_intent_locks.py tests/unit/test_host_guard.py tests/unit/test_host_daemon_startup.py -m 'not nfs and not live'`
reports395 passed in8.69s, no skips. Actual zero-cap USER-namespace checks cover
search-only DAC traversal and all four mixed UID positions on nondumpable tasks;
negative tests cover parent/leaf symlinks, malformed/duplicate UID fields, birth/
UID changes, unclassified processes and unavailable/vanished facts. Ruff,
targeted Pyrefly,216 human/29 helper documentation alignment and diff checks pass.
The first new Linux test exposed inherited-pipe cleanup ordering; all owned
children are now released before waits, and the complete focused run passes.
No fixture/loaded-policy change, full gate, original-key replay or commit occurs
from the source agent. A new single strict gate is required for these changed
technical inputs; source4/gate4 cannot qualify them.

The remaining browser causal-refusal/lost-ack finite drivers are privately
prepared and syntax-checked, unexecuted and explicitly pinned to source4 pending
new gated artifact rebinding. Exact predecessor registry code is retained under
`/var/tmp/web033-validation/old-browser-reader`; original/copy reader SHA256
7bcea7819af3f632e70cfbfdb3e2e4d0d229df9f267e0186efa36a076f7fbec2.
The next installed availability observer will export verbatim migrated schema2
storage before POST, along with its independently recorded SHA, for this old
reader's zero-write format-refusal check. It is not a parallel old-UI deployment
or a claim of full old-UI/bootstrap compatibility. No synthetic input is counted
as installed evidence and no unchanged source suite is repeated for that check.

Strict gate5 passes1459.19s on all1282 unchanged names/hashes. Normal backend
pytest summary is9790 passed/52 deselected in1155.21s. Build and all three locked
wheel installation/import/help/version profiles pass, as do179 generated wire
definitions,3809 required web unit tests/4169 combined checks,16 built-browser
checks, actual200% zoom and real HTTP/API React read fixture. Required sandbox/
functional metadata checks report23/19 passing with no skips. No optional
instrumented functional runner is invoked. Result/log/shadow-result SHA256 are
61ec12666b69459a69377d56f01a47379681b38a26054d17d3bedc289a2087ef /
63eafcdfcd1415b489558055160695df3656953d8f14ffc9218221b44440c10e /
ded86311774ab4d8e5d72308ccdd790f073fd5dd5c9db94b01d98bd4f2c4fef3.
Exact gated task bytes are retained in `gated-task-record5.txt`, SHA256
cadaadf53df46c1066d59f205a2459f6edd1fdb7801f1ea1c1b5e5f839586db9.
These are source proofs; source4 remains selected in the owned fixture with all
six grants false and both archive mounts RO. Source5 is not yet built/installed.
Only factual task/selector evidence changes follow the gate before scoped docs
checks and the clean detached source cut; main remains7894540.

Offline copied-target SELinux comparison uses separate retained baseline0a5e
and candidate6b758 inputs, UID1000 and no-reload compilation. Strict expansion
fails38 assertions in each; the full diagnostics are identical after normalizing
only private-copy prefixes and helper-source line offsets. This repeats standing
stock-policy conflicts and is not a strict-neverallow pass. Raw baseline/candidate
log SHA256 are15e19529869581336699bc796595975c63d8a052608cff22055321e417de8e61 /
2b962ee754853c9744c842674da9122eb8dae1dc7458f7a8fc756512e10ae1ab.
Separate, never-installed AV-analysis copies permit binary queries while keeping
all strict failures intact.26 finite checks pass at freshly recorded active
`domain_can_mmap_files=false`: helper/observer payload-file denials stay exact,
needed kernel/daemon proc metadata rights are present, process/symlink/capability
rights stay unchanged,819 domain members stay exact and all four distinct payload
object types remain excluded from that attribute. Effective-AV evidence SHA256
537c327814f4e564b5c7bb11bb55db5f8c20d925b977fd9645d51638b2d91087
is scoped to copied target TE/current booleans; it is not MLS/MCS/DAC/mount/
namespace/seccomp or actual installed enforcement. Initial root-PATH capture and
empty private-store setup failures remain preserved and are never counted as
policy validation. Correct populated-store inputs are independently verified.
Original host policy-store metadata/bytes, loaded kernel policy and Enforcing
remain exact; independent no-change proof SHA256
626b9698bbe53e07b3c93bc078f1111b785608a28ef229da20126696b288b54c.
No host or guest policy installation, grant change, app job or production effect
occurs in this offline comparison. Actual matching guest policy/receipt/index,
Enforcing proc-state review and independent payload denials remain required.


2026-11-04 continuation: clean detached source5
`cb1c4924732819afcfa6ea8beade3840be915b19` builds reproducibly with official
native tooling. Index/UI/wheel SHA256 are
c5bcf93ff999e10e28b1a4834f912ae6d0339ac4adcd64609224d7a8ce46125d /
448283bf70204351ec2e8b5aa0ffab7e9c0b2d2ddd1cfcc3844c7d349d9b226d /
df2d9a7a5d67a79e6a5c2d9dc5635a9dac574a055bac76a1a5ee7a170ac65570.
Build evidence SHA256
6fb85b4a1440f5d9e4a19a30d2548d83b7505f98781e8acccebc65c239df557a.
Matching app image844c56da builds and its actual confined foundation check
passes, proof SHA256
a90e8b2da4157617d881b7c976aaccb7c01d6f94eccb6f181c171964a496c1ad.
Image transfer/rootless workload acceptance remains pending.

Owned guest only: fresh protected configuration/store/SELinux backup and actual
native executor drain pass (result SHA256
384624fd23b2cfe11a819a1468badb03e9d908e90590b91280e80a1ed1835e40).
Source4 release/selector retain all7007 original inodes and bytes by same-filesystem
rename; they require restoring original paths plus matching authority under drain
before reuse. One semanage read-lock mtime refresh is explained in its separate
qualification receipt; original drain evidence stays unchanged. Official source5
stage/switch pass. The temporarily started inert UID983 infrastructure cohort is
then fully drained, including original process/task/cgroup closure; final result
SHA256 0ef15ec724312180840d98e159a72fce2bbbb93249877d86f1f7474f1c7c4119.

Root-reviewed helper peer/CIL/receipt replacement passes in the owned guest.
Old three leaves retain their original inodes/xattrs; full backup and exact old
module plus rollback procedure precede policy effects. Only reviewed module
checksum changes, with all booleans, file-context rules, masks, credentials,
operation state and hardening preserved. Result SHA256
de4bad04f98fa7df9934fb37cbd05a0e1fbe70cdf6cbd9ebe0365b2cf72968d3;
loaded guest kernel policy SHA256
9371de0fda3d0df528577dc66b4b44e7c960151815516a3b63df625cb00dac3f.
This is actual module installation, not yet actual metadata/payload acceptance.

Matching bootstrap5 rebind passes5.50s under complete cohort closure and original
noncreating exclusive global flock. Retained server/index/policy keep original
inodes/xattrs. New server changes only UI manifest; new deployment binds exact
source5 helper/modules/receipt, with all six grants false. Deployment SHA256
207baf38b0e7335359b26eb89a32d2ba5a015ed7bddf94c3e4ff4829cc826857;
policy SHA256 f8cfdc1cc272833278936e08e1b4debf455018f0cf1bcf354dc0aff16666ebbf.
Outer execution evidence `/var/tmp/web-033-fixture/native-bootstrap5.json`
SHA256 2ea189dad70dae5d802d44bb4c5928d7cc2a7a34db9d60f92cd425b19aa9c4e6.
Original global27:1706, companion27:2004 and operation-store locks remain exact;
no activation or companion recreation occurs. All services remain stopped,
both owned NFS mounts remain read-only and Enforcing remains active. Actual
installed metadata/retirement, independent payload denials and writer matrix
remain required. No production deployment, repair, job or permission change has
occurred; historical failed POST handles remain preserved without replay.


Matching source5 guarded/manual sibling manifests pass official pure validation
and transfer35 files to new private owned-guest paths; OCI archive transfer also
passes exact bytes/SHA verification. App OCI SHA256
0dcb8c9b7e89316bff66dcecbef270299ab6ceeb3b11c01f44d6b9c9c94c7012;
sibling manifest SHA256 guarded/manual
56bc39c907a6660ebf6280f41378c65dd92422259ec7211e3bcb87e217fdfce5 /
e12c281c56c4ffbd09d50a70f531bd6056840a2451522ecd2985e30834ffd57c.
No import, rootless manager start, stage, selection or activation follows from
transfer. Independent guest read verifies bootstrap result SHA256
a3dcc3761e15a19bb6c8b58c00b83474c886a7f8916715f00dd8be07a99bdbbc.
Postgate factual task/selector documentation checks pass8.03s, log SHA256
5160f973ec6b76f776eb9f3246b3344be594a7fc98d76bf456318e8a92bedc21,
with the live NAS excluded by a private read-only shadow. No technical input
changes follow strict gate5.


Actual source5 Enforcing payload-canary qualification passes10.61s in the owned
guest: helper_t and sync_observer_t each read one public usr_t control byte and
receive EACCES for four ordinary world-readable, nonsecret files labelled nfs_t,
archive_t, secret_t and Hub-state_t. Eight fresh audit records join exact PID,
inode and full source/target SID with permissive=0. Both new bounded system
one-shots naturally exit0 and original process/task/cgroups close; canonical
services remain stopped until this completes. No real payload is read, no
mmap/fallback is attempted and no policy, boolean, file-context rule or grant
changes. Raw evidence `/var/tmp/web-033-fixture/native-source5-canary-probes1.json`
SHA256 4f6aa06367e3168f0486a56654e220a6f5165e083dbf6d27252b3dab0c09c771.
Root's additional external steady-capability assertion fails because the helper
parent capture precedes the immutable child READY: parent I/A80 is startup state;
child READY/result strictly assert steady I/A0, E/P/Bc0 before any canary opens.
Observer external capture has all caps0. Both this failed corroboration and its
read-only timing diagnostic remain preserved; no external steady-helper claim,
repeat probe or assertion weakening follows. This is finite installed MAC/file
qualification, separate from actual canonical retirement and rootless role proof.

Ordered source5 native startup passes2.39s: helperNotifyREADY precedes private
worker, API and proxy. Same-PID/start-tick bounded observation handles TypeSimple
sandbox settlement without restart. Actual helper12607 has helper_t/I/A0/E/P/Bc0;
worker12625/API12635/proxy12644 retain all caps0 and NNP1. Original lock/state,
allfalse policy and RO mount rows remain exact. Startup outer SHA256
587ac49f6651a65806a6f1a774cbd813d7065fd0e1b8b438abae5c66120b1fa2.
Six actual verified-TLS Basic GETs pass6.06s at root and management prefixes,
joining sourcecb1c/UI4482, false archive/Hub/control/writable and private worker
PROBE true; selected Argon2 verifier is checked in RAM against the known owned
fixture donor. Credential metadata and all store bytes remain unchanged. Read
outer SHA256 623d3ddb5d06447d2a90930b8650506a9e018932cf14f1cd37f2df0661ab6d91.
Native browser availability4 is running; no result is yet claimed. Production
remains unchanged; no real old-key replay or archive workload has occurred.


Native availability4 is a preserved partial failure, not an all-browser pass.
Chromium root and management cases both pass real installed accessible archive/
Hub unavailability, zero job POSTs, browser1-to2 handle migration, explicit own-key
retirement200 with historical uncertainty, and GET-only reload with exact handles.
The repaired whole-executor review therefore succeeds through actual confined
helper/API paths; earlier503 originals remain untouched. Firefox root authenticates
UI401-to200/bootstrap200, then first API readinessGET401 stops before migration
or POST. Raw trace/report remain retained; challenge/protection-space diagnosis
must precede a driver or product repair. Do not repeat either completed Chromium
retirement or waive the missing browser cases. Report SHA256
14ccd576149e7adad115ff8ad0907e5f68700a549aa18c9c330fafb82bc9f63b;
outer failed attempt SHA256
e71bd7ed24c27417adce08f9dcc6a8015a051754166583b5818c86060408adc8.

Separate read-only closure verifies container669c76d0 exited1/PID0, browser
contexts/browsers and cgroups closed, exact original fixed/private metadata,
native PIDs and mount rows; no admitted job/store receipt. Marker SHA256
3775e3686ddbe70e0df1bb8a358debf0e7b7ce74ee13b47435c86ac2c231b9fb
holds exactly two retired_unknown dispositions. Closure outer SHA256
b9ef2717a7a8afe2397a52547931d61a38b151764d519ae5c1b996c26cfbb436.
Remaining browser cases are Firefox/WebKit root+management; causal refusal and
lost-ack launchers stay HOLD because their expected six completed retirements
are not established. No grant, source/policy or production change follows.

Verbatim installed exports are retained locally in
`/var/tmp/web033-validation/installed-native-availability4-exports` with exact
independent report-joined SHA/length verification. Chromium root seed/migrated
SHA256 29a99092466a6d9dde3e37e7cc154d8671dad8b83e6f693d09583b1e66d895ea /
79078dcb8a78b60471108121f1b8007fbcc202e5747c5b47870eb648c250092c.
The exact retained predecessorc23abba registry reader7bcea781 accepts the actual
original schema1 copy as ready, refuses actual installed schema2 as corrupt, and
performs zero writes to either; original handles/authority/identity/summary
fields survive migration. This completes that narrow installed browser-format
drill, not full predecessor UI/bootstrap or server rollback acceptance.


Read-only Firefox authentication diagnostic completes125.41s in both prefixes,
with zero POST/storage seeds and exact existing two dispositions/fixed/private/
native PID/mount preservation. Container580079ad exits0/PID0 and browser cgroups
close. Outer/result-report SHA256
5305b08cc56ca67caa28d90cbdf62b308caf50e0c41bef2c830d0ffc0d0859fb /
195815e5fc0bef2c72af7d254aea87d3fbdc36fc69c62746e8f608a0c7af5d7d.
Initial Firefox UI challenge401-to200 succeeds; original readiness observer
reports401 with no request Authorization and combined Basic/Bearer challenge.
No natural200 response event is observed through the full35s window. Before
any extra read/navigation, however, ordinary settled UI displays the exact
Hub-disabled explanation and disabled submit in both prefixes. Code review
joins that explanation exclusively to a typed successful readiness result;
bootstrap has no fallback that can produce it. Later explicit same-origin
readiness fetch returns200 with browser-managed Basic before API navigation;
no headers or credentials are injected. This distinguishes the observer's
first response event from the application's decoded observation; it does not
invent an original200 event. A minimal ordinary-UI readiness observation
correction is being reviewed for the four uncompleted cases. No product/auth
contract/source change follows this diagnostic. Original partial failure and
all two completed retirements remain preserved without replay.


High-effort review confirms no product repair is warranted for the first Firefox
response event: strict client success requires fetch status200 and decoded
JobReadiness; only that success assigns readiness, and the exact Hub-disabled
reason has no bootstrap/fallback source. The original UI snapshots precede all
extra diagnostic API reads. Private availability5 observer changes only initial
observation: retain first200/401 event separately, require ordinary typed Hub
reason plus disabled Submit/accessibility description and enabled Recheck, and
claim no unseen natural200 event. No extra API read, credential/header injection
or cache priming is introduced. Subsequent existing wire/status assertions and
actual retirement200/reload/no-replay checks remain strict.

Four-case continuation5 (Firefox/WebKit root+management only) is running from
reviewed driver SHA256
5ab930f6367ad5e85c00cab4a89ba0558da1cde3e7ac81e7ae8ec90c25dbfeb4
and launcher SHA256
8c9fa3458e5c492d96cb0c479e261132a3453881849a6c445c4ae766b2ec32fe.
It pins initial marker3775 and preserves both complete existing dispositions;
only four fresh own-key retirements may add entries, with final six required.
No result is yet claimed. Chromium completed cases are not repeated. Technical
repository inputs remain exactly those of green strict gate5.


Availability5 continuation passes138.06s: four fresh Firefox/WebKit root and
management cases all pass accessible disabled-job reasons/zero job POSTs,
verbatim schema1-to2 migration with original handles, explicit retired_unknown
HTTP200 and ordinary historical-uncertainty explanation, plus GET-only reload.
Both prior Chromium dispositions remain exactly unchanged; four fresh entries
produce six total retired_unknown, marker SHA256
15ac6e7bb11a45f899a0eda710868f896df4bfc467cbb28e27734f0a49ebfc41.
Original partial availability4 remains failed; its two successful Chromium cases
plus this four-case continuation establish all three browsers/both prefixes
without replay. Report/outer SHA256
51219f32deb4f1084bd06ddef7a9e427f3b91d351721c7286c682f6cb46d94f1 /
987bd94e81b23ce60bab5059dc1d9bbd028cfc4c22e50a06ee98c25cf1d1e5ee.
Browsera2615d87 exits0/PID0 and cgroups close; original fixed/private metadata,
native PIDs, credentials, both store locks/initial activation and mount rows
remain exact. No admitted job or archive write occurs. All6 grants stay false
and Enforcing stays active. Causal current-submission refusal, real admitted
lost acknowledgement, rootless writer and rollback acceptance remain pending;
this is not WEB-033 completion or production acceptance.


Before scoped Hub-only native checks, actual selected strict config validates
zero repositories and UUIDfc118; config SHA256
8838be3639b8500c30a78a138d7e92cf4288868a397965dd8a8bd361b07c4d8a.
This bounds real installed Plan admission later to empty installed selection;
no Hub fetch or archive write is needed. Root reviews exact fixed8phase Hub
transition hook, adding noncreating original-FD fstat and exclusive fdinfo proof.
Hook SHA256 fb173cfc773407336dc6ff7ce76f7c47774a6dd4f8bbea8e70e90b838a4ffffa.
It uses same-filesystem RENAME_EXCHANGE with original policy61323730 retained,
changes only Hub, preserves original locks/Enforcing and both NFS-ro mounts,
and keeps all five other grants false. No automatic schedule or production
authority changes. Each explicit grant/readiness/revoke sequence is root-controlled;
browser cannot execute the hook or submit until root's public continuation.

Chromium causal5 both-prefix cases pass51.71s: UI first observes typed positive
readiness; root then revokes Hub under original global EX before either POST.
Each fresh original Plan request receives typed pre-admission403/closed, becomes
not_admitted permission_denied, and GET-only reload preserves its original key,
record and disposition. Exactly one explicit job POST per case; no admitted
receipt/archive job. Six retired originals remain exact, with two new denial
fences: marker SHA256
f5c67474b5fa62c61636876294a46aca18ca451c656c0550098255c6b2fdb72a.
Browser10ebdb7d exits0/PID0/cgroups closed; original fixed/private metadata,
native PIDs, mounts and store locks stay exact. Original policy inode61323730
and allfalse f8cfd bytes are restored after the reviewed revoke. Report/outer
SHA256 b1e6088166124b4a398fd45e1594d4337f39c4f9cd47dd39190cacb62fb74565 /
fcd3bc2f30ae9745452b6bd43837f7e8f49bd8ad621b35b737abeac96e887824.
Firefox causal5 is running with the actual preceding Chromium receipt hash;
no Firefox result or later lost-ack admission is yet claimed.


Firefox causal5 is preserved as failed observer evidence, not a browser pass:
original root record30f2875d47d14a14b9bb04fe00c03098/key
3dae2973-b5cd-47cf-8c9b-1501558bae95 sends one POST; management sends none.
Exposed event status401 pairs with bodyHFAPI002 (permission denial); the
observer asserts401 !=403 and stops. Current permanent store nevertheless has
one new permission_denied/not_admitted fence, for nine total entries, marker
SHA256 27c3241afadd826f1bc33baea0b8ca2b704cafaf1126df73066d6f56ae6352fb.
The original prepared export, body, key and failed report59e137e53ca79d8a9fd727c4b73be0647510e9b20730f8284bcb027bf367d6fd
remain retained; the original request is never replayed. Independent closure
passes: browser90ff2e1f exits1/PID0/cgroups empty, both contexts/browsers closed,
fixed/private/native PIDs/mounts unchanged, original allfalse policy61323730/f8
restored, no admitted receipt or archive effect. Closure outer SHA256
218e6e13c0e54c3d3aa78f8161286c040161a82d77a00b477eaacd21828519da.

Plan execution-focus5/7 strategy change is explicitly reviewed at high effort:
stop repeating first-event HTTP assertions after the two named Firefox observer
failures. Use passing actual Chromium causal refusal at both prefixes for the
server admission boundary, and supported GET-only recovery of the already
transmitted Firefox original. Do not multiply this server race into additional
Firefox-management/WebKit causal POSTs solely for a uniform matrix. This does
not waive any mandatory source gate, claim the failed Firefox phase passed, or
reduce ordinary all-three-browser/both-prefix availability/recovery and planned
real-admission lost-ack checks. No product/auth change is justified by the
observer's contradictory projected event/body.

Root prepares a separate reviewed Hub continuation for lost-ack only, retaining
original hook5 and all its four executed grant/revoke records unchanged. It
requires original policy61323730/f8, existing granted standby86241728/793,
actual prior revoke-firefox, absence of unused WebKit phase files, current
Enforcing/kernel/source bindings and original EX descriptor proof. Only
explicit grant-lost-ack/restore remain; no redundant causal toggles or posts.
Hook6 SHA256 541238e2e916f944954b443fdab1bc5b05e413c98dc34729d4e385c5f5d660c7.
It is unexecuted pending fresh original GET recovery and root review. Both NFS
aliases remain RO, all6 current grants false, credentials/masks/hardening and
production remain unchanged. Lost6 will preserve the actual nine fences and
observe six fresh empty-selection Plan admissions/results, without job replay.


GET-only Firefox recovery1 is retained as a failed expectation, outer SHA256
12ad3e96d839a7ceac3fe2aff1b47b574c992fe9c7e2cb6fc837a513f607193e.
It restores the exact genuine prepared record and sends only GETs; its wait for
not_admitted times out after an original-own-key automatic GET. This is not
permission to relax the product's disposition predicate: registry1458–1480
correctly keeps a restored record uncertain when a server denial lacks saved
causal-response proof. A later denial cannot establish older nonexecution. The
pre-effect export deliberately has null disposition and cannot reconstruct a
lost response. Existing canReviewOriginal350–377 permits supported Review for
this same-scope Basic key with no operation ID. No source repair is justified.

The bounded read-only follow-up therefore checks the correct contract: preserve
original record/key/authority and unknown outcome, keep new job submission
blocked, offer Review, observe the same server permission-denial fence by an
own-key GET, and reload using reads without donating that GET as causal proof.
It will not click retirement, submit a replacement request, fabricate a saved
refusal or label unknown history nonexecution. Six actual exclusive retirement
workflows already qualify that separate action. The failed1 report, exact
prepared wrapper and all nine server entries remain retained. Lost-ack starts
only after independent prior-container closure and this corrected uncertainty
observation, with a separately reviewed continuation receipt; no result is
claimed yet and all6 current permissions remain false/NFS stays RO.


Independent failed recovery1 closure passes (browser85543e67 exits1/PID0,
original processes/cgroups closed, only GET/HEAD and fixed/private/native PIDs/
marker fullmetadata/mounts unchanged), outer SHA256
31661f76a656841ffdaab59aae98288e2820ea7bc3996fb7aef765c0f4719fcb.
Corrected recovery2 then passes32.68s from exact genuine prepared record,
without modifying any causal field: ordinary UI remains uncertain/null
disposition with original ID/key/authority/createdAt, disabled Submit and
enabled Review. A separate browser-native own-key fetch returns actual200 and
strict server not_admitted/permission_denied for that same key. The UI stays
uncertain; a second GET-only reload preserves it and its Review action. No
POST, replacement key, inferred nonexecution or causal-proof donation occurs.
Original nine server entries/fullmetadata, store locks, allfalse policy,
credentials, native PIDs and both RO mount rows remain exact; browser6a8766ca
exits0/PID0/cgroups closed. Report/outer SHA256
7456ff8a6cbfba1feb9caa9e79434ab5d60ce0784ee130c786e45a314e0d5ea9 /
225fd2d5d32c9d6eb00f9a43b2f670be86215401647b6770680610c1ed10529b.
Independent actual guest result SHA256
bdff2c0d8654a19c30df7a0ae5a854c427dfc7bde8f1c16550df90f5f329aa08.
This establishes correct historical-uncertainty recovery, not a passing Firefox
causal-submission capture or invented knowledge of the original response.

Lost-ack6 is now running after the explicit root-reviewed Hub-only grant using
hook6. Strict selected empty-repository config remains the bound; archive and
all four other grants stay false, both NFS aliases RO and Enforcing unchanged.
The reviewed launcher86549902cd3d1ef8bcfd35d01799952ff40afa0492b74f726a56137bc4375ec0
requires the actual successful recovery2 receipt and original marker27c nine
entries, preserving all while admitting six fresh empty-selection Plan jobs.
Every original key is durably exported before its one request; original real
202/opID is retained before response loss, then ordinary original-ID recovery
and terminal result must use GETs only. Actual outcome is not yet claimed;
original policy restoration follows successful closure/result inspection only,
with no automatic rollback after uncertainty. Production remains unchanged.


Actual native lost-ack6 passes204.69s, all three browsers/root+management. Six
fresh empty-selection Plan admissions each produce a distinct real202/original
operation ID, then the browser acknowledgement is withheld once. Every browser
preserves its original record/key, reloads by GET-only original lookup and
observes that exact original terminal result; a second reload preserves it.
Exactly one explicit Plan POST per case, zero replay. All six actual receipts
succeed/exit0, independently read and hashed; original IDs are
a2ffa47d078eb16e16efc4f23eb2391c,36cc9c040d0b08a1338d07e4b009ffcc,
7258e39bf5fdc2b1560764309a40ac5a,c3573bb3443f6577721f8594e9767311,
db849104789b99f3cff2287e8c06c8e6,0012c8621b595ec777d3a3b0422816cb.
Report/actual guest result SHA256
ee2021e4a733cafc05bf383a56fd4193d69c19481f1cb3db534256a11a00e20d /
048e560684de5705f10126352b7d74c287af77c654371b000238a1ffb6279c96.
Browser427b8bc7 exits0/PID0/cgroups closed, original fixed/credential/native
PID/mount evidence exact, all nine permanent fences remain byte-identical27c.
Root then explicitly restores allfalse original policy61323730/f8 using hook6;
only Hub changed during the fixture check, no archive write/other grant or
production effect. Complete reviewed grant/browser/restore evidence outer SHA256
4da930bf5631af6e4855e623b0ae75d87de928fd6c083203a873c90dc7436e09.
Native ordinary readiness/migration/retirement and real-admission GET-only
recovery now have all-three-browser/both-prefix evidence; causal refusal keeps
its exact Chromium both-prefix scope and preserved Firefox historical-unknown
qualification, without an invented all-six causal-phase pass.

Populated durable-format compatibility drill passes1.57s using a fresh snapshot
of the actual six terminal receipts/results and nine fences. Noncreating original
global/API/worker flocks are retained only for coherent copies and released
before isolated readers. Current installed reader lists/reads all six successful
original IDs/results and projects all nine fences. Exact installed predecessor
c23abba/oldwheel3b9a/operationse4cf reads all six exact original IDs/results,
while list/expire/key lookup/admission each refuses HFAPI014 before the admission
snapshot callback. Old-reader scope is this library/durable-format drill, not an
old HTTP daemon/UI/profile startup. Original and copied bytes/metadata/inodes/
xattrs, oldsite/wheel, dependency metadata/RECORDs and mounted read-only state
remain unchanged. Dependencies SHA256
32cc5e4a622a32235f064d1447b06af32bbc4ccd9d1fbe2938429b184d649d2a;
outer SHA256 65e9dccc8a9b189b8024555caebdf826d679b539d4ada5263018d8314daed158.
Existing empty-marker and exact browser-reader proofs remain separately scoped.

Fresh post-native rootless-transition snapshot passes1.03s, actual guest file
`/root/web033-pre-rootless-source5-readonly1.json`, SHA256
28165ae85c4da3dce488d8c895ed815eedd8d71c74d3d8a0b23337749181d9a7;
outer SHA256 aae83377055189680ee61107907dfc0826171eff65bbb99c539afe3d9da39176.
Six terminal receipt/result pairs and nine fences remain present; only the two
expected native API/worker UID983 actors exist. Four native PIDs remain
12607/12625/12635/12644, user983 manager inactive, guard loaded/inactive/dead,
no pending protected effects, allfalse policy, original locks and both RO aliases
stable. Root capacity14.62GB and available RAM789484KiB,8443 unbound. Of nine
rootless execution bindings only the native system target link exists; the
other eight are absent. Inherited bridge drop-in50-hfcache-readonly.conf remains
inode103339777/SHA5ba98b33b3de1b22e9a3ebe5530a358d6416322244bcd184fd83bba2b92898c8
and will be preserved; it is not permission to start a guard-dependent bridge.
No UID983 PAM/engine/import/stage, profile switch, archive write or production
action follows this snapshot. Protected post-native backup/drain is prepared
next, retaining all newly admitted original evidence before any profile effects.


Post-native protected rootless preparation now has actual effects, superseding
only the pending preparation state above. Protected coordinated native backup
and drain passes110.18s; root0600 tar785623040B includes whole native prefix,
configuration, original stores, six terminal receipts and nine fences; tar compare
passes. All native executors/tasks/cgroups and UID983 actors close before original
global27:1706 EX proof. First attempt stopped before effects on unordered systemd
relation output; qualified comparison sorts only those set-valued properties and
preserves raw evidence. Successful outer SHA256
b25102ba6d744ffe518a66f6552c2adfc68b02419ea362c5296ca27d284f2e32;
actual guest result1dc97abebd5f21e5b868e5988d28b1287bfe0c28998bf1aeaeaf7906832b46b6.
Native prefix and selector remain in place, all grants false and both NFS aliases RO.

Explicit inert user manager startup passes0.94s after no-HF-autostart inventory;
manager PID21205, applications/helper/guard remain stopped. Outer SHA256
94c769a4e54e5f6f6dda63f09b172297cc4d01ce0fb91d7d3b1f7a812a5c788d.
Read-only engine inspection passes1.59s: all four known predecessor containers
exited/PID0, three predecessor images retained, source5 image absent, six original
secret records present. Outer SHA256
5f05f72e06dcf303b85e229e995bb81983aee81580d14cd81dc84a47b847124b.
The initial secret-list observer JSON syntax failure is retained separately;
qualified JSONL formatting changes no product or engine state.

Cached rootless PUBLIC TLS certificate expired Nov1. Existing renewed native
public leaf723da338... verifies against current fixture CA and has the exact same
public key. Reviewed certificate-only transition passes1.79s using official
UID983 podman secret create --replace with PUBLIC leaf bytes in RAM/stdin.
Before that command, coherent private secret-store tar/compare and manual offline
rollback instructions are retained; both original JSON leaves are retained by
same-filesystem RENAME_NOREPLACE with original inodes/bytes/xattrs. Canonical
copies precede the official command, and both original secret mutex FDs are
released before Podman acquires them. New public-cert secret ID
99b5d354b72aa1186722f5df0; the other five complete secret identities, metadata and
encoded values compare exactly in memory without decoding or reporting them.
Original mutex inodes110972993/119585601 remain canonical; original global,
companion, store locks, credentials/HMAC, authority, marker, mounts, policy and
old containers/images remain unchanged. Outer evidence SHA256
249335df9328996575737273b981a435e5b242587f4fe6a37d6b2565144b1ff2.
No source change, policy reload, image import, profile selection, application
startup, archive write or production effect occurred. Actual fresh TLS handshake
and rootless writer/rollback acceptance remain pending.


Exact source5 OCI import and four predecessor container retentions pass14.51s.
Root opens the pinned private OCI0dcb...66336768B and official UID983 Podman
loads it once via stdin, without pull. Actual image844c56da... is added; all three
predecessor images remain unchanged. The four original exited/PID0 container IDs
are preserved by official ID-based rename to web033-pre-source5-prewarm6,
web033-pre-source5-verification, web033-pre-source5-caddy and
web033-pre-source5-api; original images/exit states/labels remain exact. No
container removal, application start, selector/unit/profile/grant or archive
effect. Original locks, stores/receipts/fences, credential metadata, native
selector, policy, mounts and kernel remain unchanged. Manual rollback preparation
and before/after evidence retained. Outer SHA256
3c08e451a46f3620363cea2736b6f29fdbc4781361ec48dc43b8c8747a6aaab4.
Fresh inert actor inventory precedes whole native-prefix/binding preservation;
rootless stage, online writer checks and production remain pending.


Fresh post-import all-four-UID membership scan passes0.485s with no exit races.
Exact inert cohort is user-manager21205/start2687095 and systemd-executor21207,
Podman pause21279 and D-Bus21288/21289; all single-task, expected parent/cgroup/
executable/context joins, no application actor. Root reviews this concrete cohort
before offline prefix preservation; any changed/unknown actor refuses. Actual
guest cohort SHA2568ae8d5cf3c6145fc9d344ec5f2e7485ffaca371d9fd24ed6c9c185e5de6c2fdb;
outer6b9ea979ec91911d42c6c64bcbf476c4963676692e585a51fb093c340a6ed227.
The successful import/retention guest result itself is
6388d1ad1d8e7b40106a9cab9a7c5b8404fa89c751fb886c422e10e4b61165ae.


Whole-prefix preservation first attempts stop before work/effects, with original
prefix/current/bindings unchanged. First precondition incorrectly required
MainPID on inactive socket units; actual diagnostic confirms systemd omits it
there, and masked inactive timers omit all three PID/cgroup properties. Qualified
preflight explicitly accepts only those observed type-specific omissions;
service PID/cgroup fields, inactive/dead states, actual cohort, masks and original
EX/no-consumer proof remain required. Failed outer SHA256
f9b2f58c2a7c50fe159cee304f131731855fb9972531e006415bb4a4c575760f;
read-only diagnostic7ce25f2f28eeeb740c1444313c5adb189961e5cf3b7e6e46b5a942e7f48502aa.
Second attempt stops at an incorrect legacy-link receipt key before work/effects;
original drain stores that map under legacy_links, not fixed. Failed outer
44203ffe8597bb486855004df194bcb8ae1e8f27aac612983a37c2e727b13df9.
Both exact executed scripts retained locally; these private preflight corrections
change no product source or gate input. Qualified preservation execution follows
only these observed corrections, without cleanup or automatic rollback.


Qualified prefix transition performs the reviewed namespace effects, then fails
its final LoadState assertion: after moving the whole native prefix and leaving
current absent, native API/socket/worker links correctly resolve to no unit.
Original command remains failed (outer9f10f59944252984bf4a2548b29c2646dfa7ec2143d3f975ae78e3c030dd8bcc).
All34529 original nodes passed post-rename byte/inode/mode/owner/mtime/xattr
comparison before binding installation, with only renamed root ctime qualified.
The nine exact rootless links and four canonical /etc masks are installed; all
original target/legacy symlinks retained, runtime masks/bridge unchanged. Original
fixed/stores/runtime checks passed before the failing final unit assertion.
Read-only diagnosticfccf119203818732479aa304ad5f19bf375b6e9688edd2ee93aa545ba04d2107
confirms empty new prefix/releases, original retained current and34529-node
inventory, exact9+4links, all roles inactive/dead/PID0, expected native not-found
units and unchanged Enforcing kernel. No stage/selection/start/archive effect.
The namespace transition is never replayed. Separate read-only final verification
checks these observed absent-unit states, all original evidence and no consumers
before any official stage. Exact executed script is retained locally and in guest
root0600 /root/web033-prefix-transition-executed3.py; manual rollback already exists.


Separate read-only prefix postconditions pass8.69s, outer SHA256
75da7b9571afc96b36ee5f1226434f9280e905b5ed8c10b8091e8f60cda74258.
All34529 original nodes including current symlinkinode86204070 retain original
bytes/inodes/modes/owners/mtimes/xattrs; whole renamed root ctime alone records
namespace movement. Exact9newlinks, retainedoldtarget/fourlegacylinks, fournew
canonical masks, originalruntime masks, allfixed/stores/credentials/RO/Enforcing
and exactfiveinertactors pass. No nativeprefixconsumer exists. Originalfailed
command remains failed and is not replayed; qualified result separately records
expected native not-found units while current is absent.

Both siblings then pass official stage2.93s, one call each under installer-owned
original EX/quiescence/NFS-ro, no caller nested flock. Private receipts0600 and
child umask022 produce protected public0755dirs/scripts and0644otherfiles.
Outer SHA256b726401bcf318f285ec0b31a7d277e91ad2e9c9d90ca01592cbecc36e81ccf82.
Guarded artifact index/runtime SHA256
be58c8587fdffa271b695b2f3ef48ec138afab2675c9865c6a32413c7f043889 /
b9e5ca09b6053d28402a72fd18c0fd96b8ea24cb9180ad992060906b9873cee8;
manual index/runtime
5415df4d42cfc78b95cfe14f2cefa1c15e6785d0e2a51c007b2a867e9057bdda /
b7274fb6a7409bedd918d52ca2342d24a035607a1cc13d430b5380c03fb24918.
Both rendered Basic origin https://127.0.0.1:8443, root_path=/management and
rootless helper983 joins verify. Current remains absent; no startup/archive write.

Read-only staged context inspection SHA256
ad343395ae8b7ab95a81db2daa168112a711ba56e950eb1ea7aa8ec8745474d1
finds new public unit/launcher artifacts usr_t with persistent usr_t. Narrow
persistent bin_t launcher and systemd_unit_file_t unit-file provisioning is
prepared only for the18newrelatedpublicleaves; no recursive/retained/archive
relabel, module reload, boolean or permission expansion follows from staging.
Actual guarded selection/helper bootstrap/activation drill/online writer and
rollback acceptance remain pending. Production unchanged.


Narrow public-artifact labels pass8.65s after actual export-shape preflight.
Three absent regular-file-only fcontext rules target only the two immutable
siblings' launchers and unit files; restorecon-F touches exactly18newpublicfiles.
Private context-files tar/compare, original local export/list and manual rollback
preparation precede effects. All280existing exported rules remain byte-identical;
only three planned rules added. Exact public bytes/inodes/modes/owners/mtimes,
non-SID xattrs and all unrelated staged leaves remain unchanged; the18SID/ctime
changes are explicit. Original semanage mutex inodes25764350/25764351 survive;
only their official metadata timestamps may refresh. Kernel9371/modules/booleans,
original API/worker stores/locks/marker/native authority/RO/cohort remain unchanged.
Outer SHA256ab12367645b78845f36aa558de9f7a779d968b9ae07d26b69d315a80bb767e82.

Official guarded selection passes1.08s, with installer sole original1706EX holder
and fresh system/user/engine/cgroup/NFS-ro quiescence. Current now selects
releases/0.3.1-guarded-readonly; no daemon reload/start/activation/mount/grant or
archive effect. Outer3b242862603224b28b40091bb1fbf940f4fa6225321e620d91878047bce69f00.
Actual source-bound rootless helper proposal passes0.60s,10874B/candidate
f6f82dea4ca93862b1374a7349e62af0640028df4ae41d5bd4fc9f318fc95c3f,
with genuine clean sourcecb1/snapshotbd39/build6fb, guarded release_id/runtimeb9e5/
indexbe58/app844/Caddyfa2/host983 joins. Proposal outer
cc82c0be20a3e00f3719fcf0b8f6719c795db4246f9fff68c593f95dc8e9a529.

Reviewed protected helper bootstrap passes1.35s: new canonical index61478371/
f6f82dea... and policy61478372/6491bdc470cdc9e022018cf612decf3eed91268123b054fdb32f50e362abb817
publish under original EX after actual offline/cohort/RO checks. All six grants
remain false. Native index61323729/207b and policy61323730/f8 retain whole bytes/
inodes/modes/owners/mtime/xattrs under rootprivate retention; native host server
stays canonical/unchanged because rootless uses immutable rendered server.
Prewritten root-owned proper-mode/SID leaves publish by nonreplacement rename;
manual rollback file and directory are synced before effects. HMAC/PHC, original
global/companion/store/runtime/instance locks, nine fences, source5 CIL/peer/SELinux
receipt, kernel and mounts remain unchanged. No policy-module reload, key reset,
helper activation, application startup or archive effect. Outer
805be97dc0a32b25c8dc8e204ab1eaca9633f23e1d0d86cfb83b6ac4bfd026ce.

Fresh first-activation-drill original-object snapshot is
792761b0d4e6a68fda6c1b279da810c1a671348f40ca3edfd237786b30ecd472:
APIroot110998247/15nodes (14files/six receipts+results/ninefences), workerroot
119616492/2nodes, original activation-backuproot128016455/7nodes, empty native
privateRuntime27:1995 and companion27:2004. Global27:1706/APIruntime27:1334/
workerinstance64515:18402599 remain canonical and must never move. Original full
snapshot is copied byte-exact for finite private preservation preparation; no
original directory/runtime/companion move or first-activation invocation yet.
Production remains unchanged; rootless online/writer/rollback acceptance pending.


Original-authority preservation passes0.995s, outer SHA256
1f64c7df348c2da02918fd9f7a54db98e911954d0e1ad9e0fa83b061ca34f5bd;
actual guest result2e4f90e5992061548fc9109f1523fbf82aa3089cfc1eda39fd3337ecdda9940b.
All three original persistent trees are retained WHOLE under root0700 local
retention; original companion2004 and empty privateRuntime1995 retained WHOLE
under root0700 SAME tmpfs27 retention. Every original node byte/inode/xattr/mode/
owner/mtime remains exact; only renamed root/companion ctime records movement.
Original global1706, external APIruntime1334 and workerinstance18402599 never move.
Six original noncreating EX guards protect coherent preservation and all close
before official handoff. Only fresh APIroot80092389/lock80092390 and workerroot
80092391/lock80092392 exist canonically:9830700 stores,0600distinct empty locks
with validated original lock metadata. Canonical backup/privateRuntime/companion
remain absent for the official command. No original fence/receipt is copied into
these fresh stores; all nine fences/six receipts/results remain intact in retained
original authority. Manual whole-object restoration procedure is durable before
moves. Private draft comparison was corrected before execution to keep original
metadata-only fixed-lock snapshots separate from content-hashed tree records.

A finite45-second live rootless observer is then armed and one separately
launched official prepare-intent-state invocation starts on those fresh stores.
The caller holds no flock and imposes no kill timeout. Exact observerready/live
root PID and sufficient remaining window precede that invocation. Actual command,
live kernel/CID/image/isolation evidence, format result and original restoration
remain to be inspected; no online use or production effect is claimed.


The ONE official fresh-store activation completes exit0/48.10s; outer
0793f8a700a44a19f49a0ba30097e5a8cc7eb00a246b5481a79950240c997890.
Actual format snapshot1b6009ee7777ec10a68bc416ef1fce0f3e007fe22e8c79cb96575fe836505262
proves empty schema1 marker with exact archive UUID, coordinated manifest with
both fresh empty-lock hashes, and new single-link0600/983 companion27:5193 labelled
archive_lock_t. FreshAPI/worker/backup/privateRuntime node counts3/2/7/1; original
global1706/APIruntime1334/workerinstance18402599 remain exact. Actual image844
container76f36963f5482d81194af990ae6a2b35c98fc076a5624c42e85c2785f4e465ab
has retained create/init/start/attach/died/remove events. These prove the actual
format invocation/image/lifecycle, not its unobserved alive isolation.

The separate observer FAILS (55.83s), outer
103c3790ba8b227f249ca84129542f2bddf08f3746e281df6e7bdcfa27b30d84;
original observations75e229077f0c3c02752f7279baab0e8b29b1bb2a82d000519076e6066ca34a26
contain0captures/0events/0inspections, only13concrete ENOENT exit races, readerexit0.
No live isolation acceptance follows. Actual timeline explains the missed phase:
observer ready19:32:34.103856/live-until19:33:19.102612; installer begins19:32:43.639883,
actual create19:33:29.642852/start19:33:29.776465, died19:33:31.185802/remove19:33:31.281853,
installer receipt19:33:31.319684. The real payload starts10.54s after the chosen
window ends. Two full release verifications/quiescence precede container creation;
why preflight/launch took46s is not established, and event-client contention is
only a hypothesis. Natural2h event projection plus file times, not a repeated
activation, establishes this timeline. Postformat/event outer
3475fe3031b1362a8bf25eb308fdac61579fd873949ef7d20b96959615ae63ac.
An earlier read-only timeline probe omitted accessible cwd and failed runuser;
its failure7806b26... is retained and corrected without any activation replay.
Absolute historical --until queries returnempty; bounded2h history projected by
actual epoch timestamps supplies the lifecycle instead. No event-parser claim.

All original authority remains protected, with all applications offline. Retain
WHOLE successful first-drill objects and failed observer evidence, then restore
WHOLE original directories/companion2004/privateRuntime1995 before any online use.
The missing isolation clause may require one separately reviewed NEW fresh-store
epoch after that restoration; neither existing epoch may be reactivated. The
bounded observation repair moves the SAME45s live window to actual fresh private
runtime/backup creation under the sole exact installer and original EX, with
passive scanning armed before preflight and no engine event client during it.
This is a named reproduced observer blocker under plan execution-focus4, not a
product/format change, delay injection or permission to replay an original job.
Source/gate inputs remain frozen; no second epoch/effect has yet been executed.


Actual whole-object original-authority restoration passes1.397s, outer SHA256
5a016aa528b989399e0a7905916852be5f807bd2721f2b5809bdf3883322be03.
One read-only running-engine query returns[] before final exactfiveactor/kernel/
cgroup closure; no engine/PAM calls occur after that final proof. Nine original/
fresh noncreating guards protect the namespace transition and finally release.
WHOLE first-drill API/worker/backup trees are retained under root0700 local
/root/web033-rootless5-intent-drill1-retained; fresh companion5193/privateRuntime5189
remain WHOLE under root0700 SAME tmpfs27 /run/web033-rootless5-intent-drill1-retained.
Every fresh byte/inode/xattr/mode/owner/mtime is preserved; original logs/failed
observer/format receipts remain separate. No original or fresh object is deleted.
WHOLE authoritative original API110998247/lock110998248, worker119616492/lock119616493,
backup128016455, companion2004 and privateRuntime1995 return to exact canonical
paths. Full original node comparisons prove bytes/inodes/xattrs/modes/owner/mtime,
six receipts/results, nine marker27c fences and original manifest unchanged;
renamed root/companion ctime deltas are explicit. Global1706/APIruntime1334/
workerinstance18402599 never moved. Guarded selection/indexf6/policy6491 allfalse,
RO aliases, Enforcing kernel and all application-off facts remain unchanged.
The result explicitly refuses any epoch1 alive-isolation qualification.

After that verified restoration, root authorizes ONE separately allocated fresh
format epoch solely to close the reproduced missing live-isolation clause under
the existing WEB-033 scope. This is neither reactivation of an existing epoch nor
replay of an original request; all epoch1 objects and failures remain retained.
The focused high review limits the repair to passive preflight observation and
an unchanged45s live window anchored to actual fresh backup/privateRuntime
creation while the exact official installer demonstrably owns original1706EX.
No engine client runs during preflight; no app pause/delay/instrumentation or
policy change. Distinct epoch2 observer work path and preflight/live receipts
preserve epoch1 evidence. Preflight itself stays bounded45s and fails closed.
Observer2a866e666517ae6f50c0bf621b23b17b9ef2b0a86007840dfc5afe47c3f33101d
is prepared/AST-checked only. Fresh epoch2 snapshot/preservation, coordinated
launch, actual isolation and another original restoration are NOT executed yet.
Production unchanged, no rootless online startup/archive job/write yet.


Epoch2 uses fresh exact original snapshot99ac5d273dbe0ca71267e452522346897a9635e60c11ae72f601f24516393398
and separately retained originals; preservation passes1.037s, outerc9912ca086a23059369ac8c6fbf6fcccc3827f8a3b83b74a4db2cc5cf84bdc4a.
No existing epoch is reactivated. Read-only5s event-reader/ps concurrency check
passes (ps0.127s while readerlive), d1fe2e4adca21ff16ff6db066162e50e58974bd7ef6dca05796b40c7811adaee;
this does not prove create-client contention. The revised observer uses no
streaming engine client, one inspect after actual kernel capture and history
only after actual installer closure. Joint launch removes human/tool handoff lag.
Epoch2 official command succeeds2.672s, but observer fails classification after
seeing exact argv/UID983/NSpid1 payload24414: assertion-only errors retained no
raw intermediate facts. Combined failed outer23b0cd4dfa28cb72570aeef1ec36c5dae3e14fb9314f50ce00ec3f85dacd4710;
observations375130d66d2a5d9146a4b52bf6a2d8d018ae36af0d5c0cd9bf28d6eec782f2cd.
Source inspection finds existing host_peer1934–1935/2111–2113 accepts exact
CID.scope OR CID.scope/container, while the private observer accepts only scope.
No product source change follows; preserve failure, capture raw data before
classification and use the existing bounded grammar. Epoch2 complete format
snapshotf3648c4607710c81010a5868a1f2cba9dfd7736c13d9d45ad716f49c9db80af4;
new companion5349/privateRuntime5347 and all fresh objects retained whole.
Original whole authority restores again1.428s, outer
f75c5c4ba60c7e4cb68ce87d2891530b8ae347a60060b268f881ba4df9f9a0b2,
guestf454deeeb6f2d275916b69c3c946832f9dfb94fae3269c02257759e9f7709554.
Original bytes/inodes/xattrs/modes/owners/mtimes/9fences/6receipts remain exact;
epoch2 isolation remains explicitly unqualified.

After that complete restoration, root reviews/authorizes ONE separately allocated
epoch3 solely for this named observer grammar/raw-evidence defect. Fresh original
snapshot47a7c55c1f5742bc3337a44573c84dd90cc89947c28bdc4e2175c3934d765f64
matches actual restoration2. Original preservation passes1.037s, outer
83297f5dea47e3320eb593bd9592381145f7824f623ae3cf08aa74607371621a,
guestc2ac12ad9a2421f21b7d2605c248ba57ebcb42cd905b6c38d2f64670f6082779.
Epoch3 raw-first observer retains candidate before classification, exact supported
optional /container cgroup, and actual SELinux label/private MCS joins. All prior
security requirements remain; no deadline extension, app delay, role grant or
product/source/gate change. All prior drafts/failures/epochs remain preserved.

ACTUAL epoch3 official activation AND live isolation pass3.309s, combined outer
ad9e147713843104f8d680e12b9c8efd2933411691f62c97a4bbcddbea9a67cf,
guest14d61748961d3135b9eaaafd8eef5a2b27d21eb208affca8169cd6e93298cfca.
Actual image844, PID24818/start3210722, CIDea41a070a396163093be049aa76c6d7f291cf6dd6b84c4b1904cc2c3e52d17d1
and /scope/container cgroup join coherently. Host UID/GID983 map from inner981;
all five capability sets0, NNP1, seccomp2/filter1 and exact worker profile08f97ff...
verify. Actual process container_t:s0:c521,c919 equals engine ProcessLabel and
private overlay MountLabel categories. PID/NET/MNT namespaces differ from host,
networknone, rootRO and tmpfs nosuid/nodev/noexec verify. Exactly five binds join
actual host inodes: fresh API/worker/backups/privateRuntime5437 RW and fixed
config61323382 RO. No NFS0:48/archive/original global/runtime/secret/Hub bind or
credential environment exists. Actual privateRuntime is not original1329;
originalglobal1706 stays canonical throughout. One live inspect plus actual
create/start/died/remove history bind the exact image/PID/CID; captured original
PID/tasks and actual cgroup close, installer exits. Observations17e5114658241ac302ef259545b8f3cd853d22b744ffd52079425136a18817fe,
raw candidate7da398485b7be5381ba050e9ee073262602114e29db9440ed0e6bc5062291a03;
qualified detail outer6f864d9d746421b0ae99ca64034fc464abb99cbeb5325ec35a8d0c9695ae6540.

Epoch3 format snapshot88facb1e7cf001bc8c74d1ce81cad4b2fa4f4156ede54c53057d3a68b2ee5ed3
proves empty UUID/schema1 marker, both fresh lock hashes in manifest, new
companion5439 and privateRuntime5437. Entire fresh third epoch is retained whole
under root/local and SAMEtmpfs retention; original whole authority restores
1.468s, outere841ed3829e22c5d61274eec41e82b0833a27f9a95546dda207a89e465be47be.
Original API/worker/store locks/6receipt-results/9fences/backup/comp2004/runtime1995
are canonical again with exact original bytes/inodes/xattrs/modes/owners/mtimes;
global1706/API1334/workerinstance18402599 never moved. Root namespace ctime
changes only reflect explained RNR moves. Nine guards release; all applications
remain offline, guarded indexf6/policy6491 allfalse/RO/kernel9371 unchanged.
Actual native+rootless offline activation isolation is now qualified; regular
rootless online/restart/no-recreation/writer/rollback acceptance still pending.
Production remains unchanged, with no rootless app startup/archive write yet.


Owned rootless source5 startup prerequisites and helper transition (2026-11-04):
Finite prestartup inspection passes; all roles/targets/bridge/guard remain inactive,
user manager21205 and its four inert actors match the pinned cohort, both NFS
aliases remain RO. Existing old flat native socket nodes are unbound and outside
the selected subdirectory socket paths; preserve them without manual unlink.
Exactly three current-boot engine coordination inodes require their existing
persistent SELinux types: alive.lck44:29 and mountpoints.lock44:58 become
engine_lock_t, SHM25:2 becomes engine_shm_t. Descriptor-bound label provisioning
passes; bodies are never read/mapped/hashed, ownership/modes/inodes/size/mtime
remain exact, only SID/ctime change. No new rule, policy load, capability or
permission grant occurs.

A coherent private local-state backup and tar compare pass under original
global/store/secret mutexes. Seven local roots include Caddy state, Hub/cache,
secret store and original API/worker stores. Private tar is root0600; no private
body/digest is disclosed. Original locks and old socket nodes remain canonical;
all guards release before helper startup. Manual recovery instructions preserve
later history/credentials and prohibit replay or automatic restoration.

Both system and user manager reloads pass under original global1706 EX; caller
releases EX before the sole system helper start. Actual helper reaches NotifyREADY,
PID25559, active/running/Resultsuccess, helper_t:s0, E/P/B=c0, I/A=0, NNP1; new
binding joins the guarded deployment and all-false policy. The original startup
script then FAILS its postcheck because it compares the complete systemd
ExecStart serialization: actual runtime PID/start_time differ from the inactive
snapshot. Read-only diagnosis confirms this is the sole hardening-field delta;
cohort/environment/fixed authority metadata and all three original stores remain
exact. Preserve the failure and active helper; no restart/retry. A separate
read-only qualification of stable executable/argv and remaining postconditions
is pending. No application role, bridge, guard, target or archive job starts.
Production remains unchanged.

Evidence SHA256 (private outer metadata receipts):
- `rootless5-guarded-prestartup1.json`: `aece46344db8cfdb9f634c43a29ef3d0ee33cb5c9b41ccc40e937bd95f306cb7`.
- `rootless5-engine-runtime-labels1.json`: `85de8d60fac52d67e5f0bb5048585fc63cc9fb3c451033c611af6e7464cfca73`.
- `rootless5-local-state-before-start1.json`: `8c8161e5676c4eca5571c35da8c3f4db5dfee0cb8b15567a980209cf8ce111d9`.
- `rootless5-helper-only-start1.json`: `0f8c5afdec3e7b281bbb060b26a2b7dbc17511ad17684ad3573c4bc81e0429ca`.
- `rootless5-helper-post-failure-readonly1.json`: `540084161dc6c75517e3f14cf9ea9d52461b866dfc2195958a06655e131cf502`.

Separate READ-ONLY helper postqualification passes0.990s, outer SHA256
2228e9303fae0a9201d15afc633f0bbc72c89050de563dfa6feb0be88e147bb7; guest result
8c5c698f9e4e28ca8f7c14623148f073732fcacafce3ff25385f315e5cae00db. Same PID25559/start3390513
remains READY; stable executable/argv and every non-runtime hardening property
match. Binding, original authority/stores/credentials/locks, current engine
labels/inodes, both RO mounts and inert manager cohort verify. Only documented
ExecStart PID/start-time fields are normalized. Original failed check retained;
no restart/reload/start/stop or engine command follows qualification. Worker,
API and Caddy remain stopped pending ordered startup.


Fresh production metadata-only reconciliation confirms the earlier independent
runtime hold: same boot45d3ce1d/current0.3.1, real NFS remains RO with
nosuid/nodev/noexec, SELinux Enforcing, four legacy writers/timers masked/inactive.
Helper/API are inactive, rootless worker failed, Caddy PID1809 remains running;
bridge and user target retain their historical active state, guard inactive.
Current-boot original global runtime lock is absent. These are existing
production conditions, not a rollout or admission proof. OPS-028 must freshly
prepare protected backups/drain/current-boot authority before any startup or
replacement; never infer an absent lock establishes executor quiescence.
Metadata-only receipt SHA256: system5edfea338a1fff0203c868f5bc593e7c714986c18e3523e4fa1ac91fcc0eb4bf,
user4bb59f398ccfde6e6de1990171cd559c6078d9e67fb0bfb60a14d6edc11dfb52.
No archive traversal, credential/configuration read, service mutation or job
occurs. Owned fixture helper qualification is separate from this host state.


ACTUAL guarded rootless worker-only startup passes4.828s. Guest receipt
28c4c43a78c89089c2732488ecaf724dd81c29d53183a16030703889298c084b;
outeree3d22d9670c0733f9ca3fda3e9d388b46b095d7503f50cb954502675cec7188.
WorkerPID25834/start3432102/CIDce8caa4ad19f3e019170d34e2417beeaf33dd3994d6a7c38fe902d5dcfe5b852
matches app844; actual conmon25831 owns NotifyREADY. Container domain/MCS
container_t:s0:c3,c100 equals engine process/private overlay labels. UID/GID981
map to host983, every capability set0, NNP1, seccomp2, networknone, distinct
namespaces, RO root/NFS0:48, exact eight reviewed binds and original instance
EX18402599 verify. Actual mode000 RO tmpfs masks and no secret/Hub bind or
token environment qualify structural credential isolation; no separate injected
negative-open probe is claimed. Original fixed authority/store bytes and inodes,
API tree and all prior receipts/fences remain preserved; only reviewed worker
local :z SID/ctime changes occur. Other roles/targets/bridge/guard remain off.

The sole next API startup FAILS8.090s before listener: actual API process25973
closes, original failed containercb18418c0c22552ef753349d6c1aa45d1409dc4a496aee75155f65112eee2503
retains exit10/PID0, NRestarts0. Worker remains same READY process; Caddy stays
off. Actual user journal reports HFAPI003 unsafe/missing/malformed credential
source at20:43:26UTC, no AVC in scoped diagnostic. Native Basic record remains
original inode11430696/root0:983/0640,206B; existing documented rootless delivery
requires actual service-owned0400/0600. Root0 is unmapped by the proved keep-id
mapping (predicted overflow65534); this prediction is not a direct failed-process
fstat. Source credential validation correctly refuses an owner outside container
root/current UID. Do not weaken it or change source/CIL/profile. A high-effort
review now scopes supported fixture-only same-PHC-byte delivery preserving the
entire original credential inode and identity; no credential repair or API retry
has yet occurred. Original API-start failure and all state remain retained.
Actual failure outerfe26fd179056df3c24b0f7eb482667b82d4f50b375495116bbb18ae63720c9d6;
guest journal/state5edc9708de1e2a4b4ea9a4eb43c01a1da3e3ebd26230b523c92fd4cb6d51df12;
credential metadata26748fb463eb3e263c95b81791a5afc08ccf2fa15aac0ed2b4eec88ccd319145.
Production remains unchanged; this fixture prerequisite is not a production
credential change or permission to reset/derive credentials.


Documented fixture rootless Basic delivery handoff passes1.042s after focused
high-effort review of containers/basic deployment contracts. Under original1706
EX, actual failed API has PID/task/cgroup closure and NRestarts0; worker/helper
remain stable and idle. Fresh private root0600 credential tar and compare are
fsynced. Original root0:983/0640 PHC inode11430696 is RENAME_NOREPLACE-retained
whole at /root/web033-rootless5-basic-delivery/original-record.json, including
all bytes/attrs/owner/mode/SID/mtime; rename-only ctime recorded. New canonical
inode11632782 is983:983/0400 with the same protected secret_t SID and EXACT
206B compared only in RAM. Subject, username and Argon2 PHC are unchanged; no
password reset, rehash, rotation, credential digest disclosure, parser/CIL/grant
change or service-writable parent occurs. Manual OFFLINE rollback instructions
retain both leaves and require fresh drain/EX before native original restoration.
Original locks remain exact. Guest93c639ad18f7c4099a6306a0477ba76d82ac49787d913e9a01600d1cb2bd99d7;
outer6e4a79be41a2b099b11108807d39fde7b175b23c7fb9941a2fbecb4b81eaa80f.

Failed containercb184... is officially renamed by exact ID to
web033-source5-api-credential-refusal1 with its entire stopped/exit10 state
preserved before a separately reviewed new API launch. New API actually runs
CIDb0092785c5f3061afbe576b7520a1e7ef5e6c08e6d0eccdd22656d375c025fc9,
PID26358/start3495678. Original literal-path listener observation TIMES OUT32.393s
because the supported application binds /proc/self/fd/6/api.sock rather than
advertising its canonical path in net/unix. Read-only diagnosis joins FD6 to
original27:1330 runtime directory, socketfile5710 to that directory and FD5 to
kernel listening socket173538. No restart/retry follows. A first read-only
qualifier also fails its assumption that Type=exec MainPID equals conmon; actual
MainPID26305/start3495610 is foreground Podman, conmon26355 and container PID
are independently joined. All failed observations remain retained.

Corrected READ-ONLY API qualification passes0.836s: exact Podman control PID/exe/
cgroup, invocation ID, actual container CID/PID/image844, mapped UID/GID981→983,
all caps0/NNP1/seccomp2, container_t:s0:c456,c576/private overlay MCS, RO root/NFS,
exact12 binds and host-inode joins, exact4 original REST/MCP/Hub secret IDs with
UID/GID9810400 and effective Basic leafowner9810400 verify. Original stores/
receipt bytes, lock inodes, worker/helper and RO mount rows remain exact.
Guest061e82d681869b6fb74ffa7d3b733f0ac88031c9febe568ac973e0315d36cdb9;
outer471a9b7903d263e640baf91aa2ec2042b8bf4ed2f9b4f52342d2af32e119aec8.
No HTTP request or job has occurred; Caddy follows only after that proof.

ACTUAL Caddy-only startup and confinement pass1.758s. Container
4c97e24c65ec15c5a1570f82a6f94941280706275635c6869279482f896f6dd1,
PID27038/start3531359, foreground Podman26992 and pinned Caddy imagefa2 join.
Real TCP8443 listener, mapped UID/GID, private container_t MCS, all caps0,
NNP1/seccomp2, RO root, exact4 binds and only original TLS-key/new public-cert
secret IDs verify. No archive/NFS mount exists in Caddy. Related local :z labels
change with original directory inodes/owners/modes retained; original API/worker
stores/locks, live API/worker/helper and both RO aliases remain exact. User target,
bridge, guard and manual socket unit remain inactive. TLS handshake/authenticated
reads/browser workflows are still pending. Production remains unchanged.
Outer84fb51018838f7fc284d3b1aa524ab1dd4d91022773dcab986e02c3383e7002f;
guestd10bc189e6d8ac96452d0effacb7d4f43f085c1345779551e9e0d1ea7e2c0571.


ACTUAL guarded rootless strict-TLS/UI/API reads pass9.308s. Selected running API
SDK independently Argon2-verifies the known fixture donor via RAM/stdin only.
The real8443 handshake verifies original CA949c, IP SAN and renewed public leaf723d
paired with the retained original key. Ten authenticated GETs all return200:
bootstrap/version/readiness/rendered Operations shell/main module asset at BOTH
root and /management. Bootstrap sourcecb1/UI448/currentarchivefc118 and exact
rendered HTML/module bytes match immutable installed artifacts. Typed readiness
observes archive/hub/control/archive_writable FALSE and verification_available
TRUE, proving actual API-origin private-worker PROBE. Original store bytes/
metadata, credential metadata and all live unit MainPIDs remain exact. No POST,
job, browser JavaScript or writer acceptance is claimed by these reads.
Guestc46a1ed74cacc40204f7b9bbae93c8d288ce277dec1172ecd0e3e9016d355485;
outer4858279eea6bb516e1dbe91ffdddc69b51839fa13ed78038dbf10ec63018bf05.
A finite resource check before sequential browser workloads finds711744KiB
MemAvailable/no swap and13.61GB available local disk. Existing managed fixture
configuration has only schema/storage/Hub top-level keys, no repository selections;
its unchanged public fileSHA8838be3639b8500c30a78a138d7e92cf4288868a397965dd8a8bd361b07c4d8a.
This supports a later bounded real empty-selection Sync writer drill, not a fake
write probe or authorization for production's configured selections.
Rootless browser recovery, writer/restart/no-recreation/refusal/rollback clauses
remain pending. Production remains unchanged.


First direct rootless browser availability phase FAILS48.028s and is retained,
outer07de0ae8ca41de827d8c7aaa6bdffc36ee5ce962fcae76ca37b9df5ec17225ba.
Actual Chromium/root typed Hub-disabled and Sync-disabled UI, accessible
Submit description, enabled explicit Recheck and zero job POSTs pass. Schema1
migrates to exact fsynced browser2 export; own-key GET returns200. The sole
explicit retirement POST returns503/HFAPI015. Preserve original record
85ccd17367bd4ff5ad949f79cc0ee108, keyb5e37d8e-4932-4730-bc78-f5733d9c26d0,
route/api/v1/plans, absent operation ID and historical uncertainty; no replay,
Hub grant, source5 browser rerun or new fence occurs. Original marker remains9
entries, original6 receipt/result pairs remain; reportd141154b2b60eb7975c0d8d0e4ad5d725ef05e060828bf35705d299885b6c6e3
records contexts/browsers closed. Separate exact browser-container/cgroup closure
still requires qualification before any subsequent effect.

Helper failure metadata joins observe-peer→_intent_auxiliary→_command nonzero
systemctl exit. Both exact fixed commands/environment pass unconfined; this is
not confined proof. Actual original user-manager PID21205 journal at21:03:46UTC
identifies sender helper_t and fixed `systemctl --user show dbus-broker.service`
DENIED service/status on system_u:object_r:dbusd_unit_file_t:s0. Generic user@
fragment/drop-in have systemd_unit_file_t, vendor broker has dbusd_unit_file_t.
The user manager's journal is authoritative even with no kernel/audit AVC entry.
Original journal receiptc3d75df198ae998004f1b99b3e265e4f7865ee0e4f99e34649cce814355f361f;
unconfined query receipt174a72b7ac5132b5ed7af32d7132464ba2f3e4a5e018b37cd74393dbb801386e.
Two separately owned fixed CLI confinement probes stop203/EXEC before their
commands and are retained as unqualified diagnostics, not a reproduced target
read. Both have PID0/no active children. No app restart, policy load or new grant
occurs. Separate Podman transient-scope start/status denials remain denied;
successful fixed inspection does not justify granting control.

Named high-effort source6 conformance repair adds EXACTLY helper→dbusd_unit_file_t
file getattr/open/read and service status. No map/exec, capability, transition,
control, selector, process skip or neverallow change. All38 neverallow forms are
byte-identical to source5. Two focused regression checks fail before repair;
all64 SELinux-policy tests pass after repair, Ruff/format/diff checks pass.
CIL726d224b9954b5ea8351483247dff4d85e98c538ee06016f78f4cebab1392c95,
test5164d94315157b5588aad8539a8c94d093145b6f6a699d472bd85056f1e38b56.
INV020, security/host contracts and ADR150/164 record the exact type-wide metadata
exposure and fixed-selector boundary, with no new architectural decision. The
source5 green gate/evidence remains historical; a fresh source6 strict gate,
matching immutable artifact/policy-receipt/bootstrap handoff and actual Enforcing
retirement plus payload-denial checks are required. No package completion or
production effect is claimed.


Source6 strict gate ACTUAL PASS1540.283s (shadow1540.567s),
`rtk scripts/check.sh --require-web`:9791 backend tests pass/52 deselected,
179 generated wire definitions,23 sandbox/19 functional-metadata tests,
3809 unit/4169 component checks and16 built real-browser checks pass with no
required skips; zoom/layout and real API React source fixtures plus build pass.
These browser checks are source fixtures, not installed product acceptance.
All1282 source names and bytes remain unchanged throughout. Gate resultSHA
fac0096c5b522604500e5edd9057fffb488d08b840eff599ea84516f46386a3b; raw log583e47c7b120d042a23d99d98c510564a1f4567943742c7ebf5f2e96818e9e10.
Source6 candidate is now gated; installed source5 runtime evidence remains
separately scoped until matching immutable handoff and new actual qualification.

Copied target-policy source5/source6 strict builds each preserve38 identical
normalized neverallow failures; neither is a strict pass. AV-only binaries both
compile,29 effective checks pass under actual domain_can_mmap_files=false:
existing26 payload/confinement checks plus broker file/status positives and
preserved unrelated manager-control denial. Broker candidate has exactly file
getattr/open/read and service status, no map/execute/write/control; all819 domains
remain unchanged. Neither binary is installed. ComparisonSHAa5338928cf83a97ae21916cab0230de24f956d9c76df2af97253832a810f0988;
AVce89817e26b88c0690ff78ba93c7eed49741277aaee6910b750e5937c4125798.
Root pure-read full-store continuity additionally passes: original /var/lib and
/etc SELinux-store inode metadata/bytes, kernel7c673c5f.../Enforcing and all331
booleans/fcontexts remain unchanged. Root receiptca85aebeac57efbfb805b2d30460eb473014a82e46c94702e6aebaee12827408.
No host policy transaction, permission change, NAS access or production effect.

Exact failed browser11364ac... closure is independently qualified: exited1,
PID0/noOOM/no cgroups, original contexts/browsers closed and nine-entry marker
unchanged. Guest5d445ae0f4a6cbc854cc6a241b8068dbd8b36ac00ea894a18844d6cc7ef4b512.

Fresh protected pre-drain critical backup ACTUAL PASS1.447s: root0600/4157440B
tar and compare under original global1706/comp2004/API/worker/secret mutexes.
It covers117-node rootless prefix,25-node /etc/hfcache, original stores/backups,
secret identities, both PHC records and exact failed browser seed/export/report.
Only metadata is disclosed; no private body digest, reset, permission or source
change. All guard FDs release BEFORE normal drain. Guestd97895bc5f2d8f260d7abe7609ef6f0e354aab14d705a84daf2970984b876336;
outerd5c6cdcf69374df8764996a2d0fefdcf9885739ac339fae7351e1eb4519dcf43.

First drain preflight refuses before effects on its too-narrow cgroup leaf
assertion; preserved outerbaa99902102d737309064b6522eb3451bf3921230afaacc371444869cb834546.
Actual paths use supported libpod-CID.scope/container. The corrected read-only
join accepts only each exact service group, exact CID scope and optional container
child, then drains the ENTIRE corresponding service/scope trees.

ACTUAL reviewed graceful retention-drain passes7.625s: proxy first, API while
worker/helper remain available, then worker and helper. Before each normal stop,
root officially renames only the exact live CID to web033-source5-online-caddy,
-api or -worker. ID/image/labels/PID/start remain joined. Existing unchanged
ExecStop sees canonical absence, preserving every CID without rm/prune. Each
normal `podman stop --time -1` completes with exit0; every original payload,
conmon/foreground process pidfd is closed and entire cgroups/tasks are empty.
All units are inactive with success, helperPID25559 closes normally, only the
original five inert UID983 actors remain. No forced kill, target/default/socket
start, helper-policy change, record replay or source change occurs. Original
1706/2004/1334/18402599/store lock inodes, all store bytes/metadata, credentials,
RO aliases/Enforcing/disabled schedules/masks and deliberate inactive guard/bridge
remain exact. Original EX guards reacquire after closure and release only after
coherent proof; every subsequent protected action must freshly reacquire.
Guestf2df9f6b89651ce7fd93c7a03be18c79e47e4b883c502a2da049e8b1bc56e36b;
outer100616ef6d6e97810cea244b93ce5903d4f14e676b355baed1f943a186b85ac9.

Post-drain private local-state backup/tar compare also passes1.196s, covering
Caddy data/config, Hub/cache, current secrets and original operation stores under
original mutexes; all roles remain off and old flat native socket nodes remain
unbound/preserved outside selected paths. Root0600 tar81920B; no archive traversal,
manual unlink, secret disclosure or policy effect. Source6 immutable cut/build,
whole source5-prefix retention and guarded installation remain next; no source6
policy has been loaded and no production change has occurred.
Outer4ef86ec9254f3b46ff99e9ac67c6aed474ce9bd8e8a003d5d285d86802fc3fa7.


Source6 immutable handoff ACTUAL: clean detached fixture source
`510e748ddbfe96169d306dee2d296e01ecb64775` (tree0848b103...), strict-gate
technical inputs unchanged; only factual task/current updates followed the gate,
with scoped documentation check7 passing. Reproduced native bundle/build passes;
web-release5244ac5f36fcc3e4cbe6588de03397ff1583c05ab628068f9082730d02a067d8,
full snapshot e1d3b97517a3884396a60a0ba1afa51b94832e33a9b6fbefb2ff98f401957e75,
UI73ebc9ca9fd2190b52df6afb3219eadad5d5066df7534b51e2886c0501978954.
The matching locally built application image is67c6cb9d810c375d907a5f80a4e02c13b505593c3e77932562926cfa65130176;
wheel df2d9a7a... is unchanged from source5. OCI66,336,768B/b9c6f2c8...
and35 sibling input files transferred to new root-private guest paths. Actual
native verification and original-lock UID983 image import pass; every old image,
tag and all8 stopped container IDs/names remain unchanged. Import guest receipt
476d2d704680ec51a4f3dd5132cd2e221928112adcb1590d494bffd67aba3840.
No image publication, main commit, package completion or production effect.

Whole source5 rootless prefix retention ACTUAL PASS: all117 nodes, original
current inode80244707, exact bytes/inodes/attributes preserved under same-FS
RENAME_NOREPLACE to `/opt/hfcache-web033-rootless-source5-retained`.
Only root-directory rename ctime changes, explicitly recorded. The original
nine dispatch bindings and all stores/credentials/coordination objects remain
unchanged; prefix FD/map ownership scan is empty. Guest receipt
8629e7a68cf5ea7f7a83e35cd622de95659650f3fc2d64190a2770108fb7075c.
Old stopped CIDs remain inspection evidence and must never restart against
reused source6 physical bind paths. Manual coherent rollback is prepared.

Both source6 immutable siblings ACTUALLY stage through the official installer,
each taking original1706EX independently after closure/NFS-ro checks. Only empty
root-owned0755 local prefix/releases scaffolding is created under a separate
released original-lock window; no caller lock overlaps official staging.
Guarded artifact index a0348ce50492346c2f4646ef3056b912b6547d285765d170bec65be92314d7d5,
runtime63a84702b0ad052f42c184cce1f7271d6dfe09fcfdaa4621b3add4d0e3b61a6f;
manual index69f0552fc7b15856f33f722da2e74fcfd72ab78f28cc5e199aa5c3f5a6cdc0a6,
runtime750b7e128f5015fd31a5d162de54a0a24849681c82fb1ae3a86465db273d93e0.
Stage receipt41d204a2ed6a321c763c68342b1dfb5dba3822f170819eaae4226b4868b28513.
Exact18 new public executable/unit leaves receive existing fixed fcontext labels;
no rule/module/boolean change or retained-tree relabel occurs. Official guarded
switch then passes, current inode111208411. All application/helper roles remain
off, both NFS aliases read-only and Enforcing intact. Matching source6 CIL/module,
receipt/independent authority handoff and actual installed recovery/writer checks
remain pending; production remains unchanged.


Source6 guarded helper handoff ACTUAL PASS11.564s: a fresh full protected
policy/configuration/helper tar is compared before effects; original CIL inode
80086300 and SELinux receipt61323727 are retained whole via RENAME_NOREPLACE.
The sole priority400 underscore module installation changes exactly CIL6b758→726d;
all other modules/booleans/local fcontexts and all15 receipt-label roles stay
unchanged. New kernel4e6b09f1ca5ce42dcc9945c259823506f7dea2694501de36d914b251b91edfda,
receipt28628f39d6f0c9c459ec8d3d1cfbcb59f661c80856083d14cbe7f817f4e3cc8d,
receiptinode61480741/CIL80090631. No library/unit/credential/store permission or
body changes; Enforcing and both aliases RO remain. Manual coherent rollback
includes the exact old underscore CIL and matching original receipt/prefix/authority.

The genuine official source6 proposal exits0 and its candidate is independently
qualified. Its original wrapper postcheck fails KeyError on an invented top-level
source_commit field; actual source lives under source.parent_commit. Preserve
that wrapper failure and saved candidate; do not rerun the command. Matching
source510/e1d3/clean/profile/image/index/runtime/CIL/receipt all join. Actual
bootstrap publishes deployment2a4e79ef47b48009458a4d2c0a9bb9f12d34eb3da90e884a7d6607a6927ddb6a
inode61480742 and all-six-false policy2f077af170801bc058b1c3c360282c2976fb1ef7aa1dfe206459fd21296afaa1
inode61480743; original index61478371/policy61478372 retained whole. Original
coordination/store/PHC inodes and histories are unchanged, with no activation epoch.

First source6 read-only startup snapshot preserves a diagnostic failure: the
retained credential-refusal CID reports Podman ps state stopped, while its
inspect State remains exited/exit10/PID0. Qualified snapshot2 accepts stopped
ONLY for that exact historical CID and separately checks its exact exit10/PID0;
all other7 remain exited/PID0, images/tags/names unchanged. Both failed read-only
local diagnostics (inherited inaccessible cwd) also remain; setting cwd=/ fixes
only diagnostic execution, no permission change. Snapshot2 passes and reports
only the planned reload/readiness/start sequence outstanding.

ACTUAL manual current-boot startup passes helper→worker→API→Caddy without any
target/bridge/guard/socket activation. Helper NotifyREADY35135/start4090297;
worker NotifyREADY35302/start4096629, conmon35299,
CID4964a3f8626c454668ae988405fe0a222b7c87ef3c60aae57ed858f6c825edf1.
Worker actual no-IP/offline/no-secret mounts, private namespaces/MCS, caps0,
original instance lock and bound listener pass. API35479/start4100297,
CIDc04fbb59a0847c720d5bbbc75ecee932904df54364cafa5a57d83cdb19a75ebd,
manager foreground Podman35427; all12 original bind joins, four original secret
identities, PHC11632782/9830400, cap0/privateMCS/RO root+NFS and held-directory
socket grammar pass. Caddy35834/start4102232,
CIDcb7486f2fb82c53d18f89ea2e5586dd037269118db42ab87373f8736d4889ecc,
foreground Podman35788, actual TCP8443/confinement/original TLS-secret mounts pass.
Only ExecStart runtime fields are excluded from stable hardening comparison;
its executable/arguments/ignore_errors and every other hardening field stay exact.

Actual source6 strict-TLS installed UI/API reads pass9.271s: ten GETs, all200,
root and /management bootstrap/version/readiness/UI shell/mainJS are exact clean
source510/UI73 identities. Actual selected API-container Argon2 verifies the
known fixture donor via RAM/stdin only, with no credential reset/disclosure.
Typed readiness shows all protected permissions/writability false and real
API-origin private-worker PROBE true. All original store bytes/metadata remain
unchanged. This is installed read/profile proof, not browser or writer acceptance.
The six-case real-browser followon is launched once: first restores the exact
prior failed Chromium/root browser2 record/key/authority verbatim, then reviews
that original; remaining five contexts are fresh. Results remain pending.
Production is unchanged; original production request remains unreplayed.


First source6 six-case followon FAILS71.579s before ANY POST: current installed
Chromium/root accessible unavailability and automatic original-key GET200 typed
unknown/opnull/dispositionnull pass. The driver incorrectly waits for uncertain;
controller explicitly maps unknown to missing, preserving the historical raw2
missing state. This is a driver expectation error, not a product/source change.
Original report2a4a98ecbeae8ba5d64bdb45d35dcd11d70e5ec22d34b60d5322ce7fb5041bc3,
CID519c9f1561fce8be0a1bd78c061a71be832b555444e9b715e4d6dcf5ecf94e18
is independently closed/PID0/noOOM/no cgroups; contexts/browsers closed. Closure
receiptf236af01f96fec5637b89115f87f225cf4fbbf2bb09e262be4ab6b75976acc89.
Nine-entry marker and original85ccd/b5e key/authority/raw2 remain unchanged.
A uniquely named followon2 corrects ONLY that expected state and requires the
failed run's actual closure receipt. It remains unexecuted at this checkpoint;
no job replay, new key, source edit or gate repetition occurs.

Source6 confined canary1 preserves a probe-only failure after the helper's five
opens and normal successful closure, before observer start. A module-level loop
variable start shadows the reused process-birth function start(fd), causing the
second cohort check to raise TypeError. All original files/units and helper
live/terminal/journal evidence remain. The observer unit has never started;
prepare an observer-only preserving continuation and independently qualify both
original-helper and observer audit/closure results, without repeating the helper
or recreating any canary. Original kernel/authority/store/credential/RO state
remains unchanged, with no application source or security-policy repair implied.


Source6 observer-only preserving continuation ACTUAL PASS6.614s, receipt308d758b6bfb53247cdb6a31923e9d834697361cdb9e644b36ffea36a2aba4cb.
It qualifies the original helper's five opens/actual PID/task/cgroup closure and
four original-cursor audit denials, then proves the existing observer never
started before its SOLE start. The observer exits0 and its exact tasks/cgroup
close naturally. All10 total opens pass: each actual helper_t/root-capC0 and
observer_t/UID983-cap0 reads the public usr_t control and is denied nfs_t,
hfcache_archive_t, secret_t and Hub-state payload reads. All8 fresh audit denials
join exact original PID, inode, SID and permissive=0. No helper repetition,
canary/file/unit recreation, reload, grant/module/boolean/fcontext change, real
payload read, mmap or engine call occurs; the original failed script/evidence
and all protected state/credentials remain. Corrected browser followon2 is now
launched once after that closed serial probe; its result remains pending.


Corrected source6 browser followon2 FAILS46.663s at the first deliberate review:
automatic original-key GET200 returns typed unknown and browser missing, preserving
record85ccd/keyb5e/originalAuthority across actual API instance change b83ae→de591.
Accessible Needs review and explicit Review availability pass. Exactly one
retirement POST returns503/HFAPI015; ZERO job POSTs, five remaining contexts not
executed. Original reportb368f2887b599c81da5c75df0f4e7b08e33e97d2ae5ffa941fce6e825fabe957
and failed CIDd96a420ce58358bca6e867cb7406f037f340eab56d31c9db772bf41e9001ca19
remain. Independent closure21b84f6e42d720a78ad2862e5fa4794b87f4e09e1230e8a321ffb6454a633c66
proves exited1/PID0/noOOM/no cgroups and browser/context closure; marker9/raw2
remain exact and no original retirement/replay is inferred.

Original helper journal advances past the repaired broker metadata query and
identifies ValueError at host_peer._intent_executors line2359, the exact
process.argv==expected container-launcher comparison. Actual fixed selected
worker unit is Type=notify and MainPID35299 is /usr/bin/conmon/start4096628;
API/Caddy Type=exec MainPIDs35427/35788 are /usr/bin/podman as expected. Unit
fragments/InvocationIDs/ControlPID0 and process/cgroup identities are joined in
rootless6-executor-mainpid-typed-metadata1.json. This is the named candidate
executor-model mismatch; analyze the smallest fail-closed notify-worker/control
join before source changes. Do not grant unrelated Podman transient system
start/status permissions: those incidental denials remain denied and are not
the recorded failing predicate. Dependent Hub/lostack and all archive effects
remain unexecuted. Source6 strict gate/artifacts and actual read/canary evidence
remain valid with their scope; any necessary technical repair requires its own
focused regression checks, fresh strict gate and immutable installed handoff.


Root independently joins full actual worker inspection to the typed controls:
State.Pid35302, State.ConmonPid35299, running/!paused, exact4964a... CID/image/name,
and Config.CreateCommand exactly equals foreground Podman35259/start4091952
argv in the fixed verification service group. Payload parent is conmon35299;
public conmon grammar pins full CID -c/-u and fixed worker name. Evidence is
rootless6-worker-inspect-control-join1.json and
rootless6-worker-conmon-public-grammar1.json; no credential/environment bodies
are captured. API/Caddy remain Type=exec/foreground Podman, worker is packaged
Type=notify/NotifyAccess=all with --sdnotify=container.

Authorize a named high-effort source7 conformance repair in WEB-033: contract
first, retain all-running closed container inventory and add only one fixed
internal worker inspection through the existing bounded typed engine child.
Preserve API/Caddy MainPID checks, exact worker foreground Podman uniqueness,
conmon/container/control/cgroup/UID/image/CreateCommand joins and original
birth/invocation revalidation. Unknown, duplicate and raced identities refuse.
No command/CID/path chosen by callers, new policy/unit/capability, budget
extension, process skip or weakened API authentication. Existing bounded whole
UID scan supplies the unique foreground match. Focused red/green regression
and format/lint checks precede ONE fresh strict gate7 after technical freeze;
matching immutable installed proof then remains required. No implementation
success, gate7 or source7 deployment is claimed at authorization. The agent
owns host_peer/tests/necessary contracts; root alone owns protected effects.


Source7 contract-first executor-model repair is implemented and root reviewed.
The new fixed internal worker-inspect branch preserves the existing all-running
inventory and original aggregate deadline/file/byte limits. The bounded whole
UID scan must find exactly one foreground command in the fixed worker group;
inspection then joins actual notify conmon MainPID/full CID/name, unique exact
indexed Podman command, payload PID1/UID/GID/caps/maps/cgroup/parent and image/
CreateCommand. All three process facts and manager invocation revalidate.
Existing API/Caddy Type=exec MainPID predicates and API authentication remain.
Prior independent manual-writer payload-domain proof is retained, not overwritten.
No conmon ELF read/open, policy/unit/capability or budget expansion occurs.

Actual-shape regression reproduces old line2359 failure before repair. Final
focused suite passes359 tests in3.77s across intent-executor/engine/peer/runtime/
locks; wrong types/monitor/payload/parent/CID/image/name/command/UID/GID/groups,
missing/duplicate/unknown actors, raced births/invocation and malformed/conflicting
internal selectors refuse. Ruff/format, focused Pyrefly0errors and diff checks
pass. Freeze receipt0f8ee741a253b9e5da979b37121a691ff929514b074140096d8221724b40d825
pins9 paths. host_peer4cda8b889b3fe9b10b9db8092c6acdfc5988b2346747f8d2c31a00981dd04036;
new test_host_intent_executors e7601f56ee57a34b35520794dc80f26393c7681845da0fed5aaebb319346b25d.
The original untracked intent-lock regression file is separately verified exact
against source6 (27c59bef...), with no deletion or rename. New source count+1.
ADR150/164, INV020/023, recovery, host and security contracts explicitly retain
closed selectors/whole-executor proof and independent protected effects. No new
architectural decision, dependency, public API/durable format or policy change.
Technical inputs are frozen for fresh strict gate7; installed source7 acceptance
and recovery remain pending and source6 stays selected in the owned VM.


Source7 strict gate ACTUAL PASS1481.871s (shadow1482.141s),
`rtk scripts/check.sh --require-web`:9826 backend pass/52 deselected in1174.90s,
three locked wheel profiles/import/help/version pass,179 wire definitions,
23 sandbox/19 functional metadata,3809 unit/4169 component and16 built browser
checks pass with no required skips. Actual200% zoom/320CSS controls and real
HTTP/API React source fixture pass; installed/Caddy/production scope is separate.
All1283 source names and bytes remain unchanged through the gate. Result SHA
658768a75c08884a525892d3292242715a8b8db99c12aa05a2618fab2a4b1639;
raw log66ca6b7bd17b4a6a87237bb2d94871749c5cf3e5b01c85ee39463c05a5c9078a.
No repeat full gate is needed without another technical source change.

During the frozen gate, fresh protected fixture backup and actual graceful
drain complete. Critical tar4771840B/root0600/inode80300614 covers17 roots:
source6 whole117-node prefix, canonical helper code/CIL/receipt/configuration,
all original stores/backups/secret identities/both PHC records and original plus
source6 failed-browser exports/reports. Tar compare and metadata continuity pass
under original global/companion/store/secret mutexes, all released before drain.
Guest0ae8c12b1694da5a2a08f163de964acf139c3446ad070459b7eb35e4ac6ef7b6;
outer4e3b4ef510bdd7be99e35c7d0718e4c6712ff2ddf4161d19570fa46a4acc2f88.

Root pre-effect review preserves the unexecuted drain draft and corrects its
known historical credential-refusal CID ps-state expectation (stopped/PID0,
inspect exit10), with all other old7 exited. It additionally requires each
newly drained role exit0/noOOM/inactive-success and empty group, and compares
all store bytes in RAM under a brief released original serialization window;
no private body digest/output, source or gate change. Actual retention-drain
passes9.497s: exact live CIDs renamed once before normal stop--time -1,
Caddy then API while worker/helper remain available, then worker/helper. All
original pidfds/tasks/complete service+libpod cgroups close normally. Preserved
names are web033-source6-online-caddy/api/worker; all11 core CIDs, old images/
tags, histories/locks/PHCs and masks remain, original5 inert983 actors unchanged.
Guest4b9c8c8f3804eafb70194b0609e719ca6047bdb2eca27ed34573639d8f2e79dd;
outerbf998e162299ee3a9de1d5f5320c88bcef12fe337fb4cc2bac0608be23c18103.
No forced kill, replay, cleanup, grant or selector/policy effect occurs.

Post-drain local-state tar/compare also passes1.112s, root0600/81920B/inode
119859810, covering Caddy data/config, Hub/cache, secrets and both stores.
Original flat socket nodes remain unbound/preserved; selected role sockets are
removed only by normal application cleanup. All six original guards release.
Guest644719fa0cfdce849f98dac03c864bf5e6be860f51ff8597910cc70e1d8cdcd9;
outer0e77ac34c596647023dae02d9316070069d8f63e97354306b84e7e13afb2fc35.
Source6 remains selected but all application/helper roles are OFF. Source7
matching immutable cut/build/install and recovery/writer/restart/rollback proof
remain pending. CIL726d/kernel4e6b/receipt2862 and source6 index2a4/policy2f07
are unchanged; source7 needs only peer-code and matching authority handoff,
with no module reload or SELinux receipt replacement. Production is unchanged.


Source7 immutable build and guarded owned-VM handoff ACTUAL (continuation):
clean detached cut861094695b0a03eeb24c5c4ca2826d961998da7b,
tree732a75e6ce9cb4b30bc61dcd90342a99a14a4e7f, preserves both untracked
regressions and the original draft. Post-gate factual task/current edits pass
docs8 in7.895s; technical source remains frozen. Main stays7894540.

Reproducible native bundle10.445s: web-release index241df59f28ec123ce675d94e561470b9045f5e9832a8be0e64f1bd60d8462894,
build evidence6cab45263c7f0250ddd051ce65ac5a2b4d2c83cd0e7fbf334ea18b2a4f96d7b0,
full source snapshot155fe15046d09eca8c82f0f81e9dd425e75ac911a76902dad98d31f29ad64d4a,
UIc4e8ea834e881a137f0e95c65e3a9f6c663965ae6348094d1b16bc2983494949,
wheel ebb7402fa9e0b1bddea6b111a026b6b885b378fb2fc1a9354311fb95b2481154.
Local application image build24.675s produces
cbda524a67c131778e85ea34801eb76308f88b048319e6325843128c31715799;
no publication. OCI export66338304B/57c175990c87559eb97784014a3e2215be4a3fbf9bcf1611311dd200da1ffb40
and exact bundle/sibling transfer verify. Rootless import7.364s preserves all
11 stopped containers and five predecessor images/tags, stores and credentials;
only matching source7 image added. Import receiptf5badbf7b90eb3ab292fb53d6b3761e52f4915d97770f13a5c636e9d07010b8d.

Whole117-node source6 prefix retained by nonreplacement rename at
/opt/hfcache-web033-rootless-source6-retained, retaining current inode111208411.
Retention receipt7e3066fa3f1ec975f6cb260026517b97ebfc3ba7898f9495b36384a4d28bbb06.
Both official stages pass2.935s under their original-lock barrier. Guarded
index7aa28b8671999030ffd35d01e7e5f2ff9f550d04e3b6be11f973c9f84efb190d,
runtimed05a1ccde892a40dcff63728d01a1964c2917732279354c6207b24fe2ed33b23;
manual index31e42b712608e8b28f22f4592e8726eebb8d739a5b71f446bfbd8bd43c32e00e,
runtime962657348287c7aede14adaf17cc16b5126077fdb4409b6fc091ac8de715de53.
Existing fcontext labels applied only to18 new public artifact leaves; no rule,
module, boolean or retained-tree relabel. Official guarded switch passes0.936s,
current inode80332352. Switch receiptbc14297846853369c23a897650e9021e58a1b4a1ae0f5714aaf5b48b4a905e9c.

Protected peer-only handoff passes3.441s after fresh protected tar/compare,
rollback preparation, whole-cohort offline proof and original1706 EX. New
canonical peer4cda8b88...04036/inode80332353; original complete source6 peer
inode80086299 retained under /root/web033-rootless-helper-source7. CIL726d,
loaded kernel4e6b and SELinux receipt2862 remain unchanged, as do source6
index2a4/policy2f07 (all six permissions false), all original lock inodes,
operation stores, credentials and nine-entry marker. All app/helper roles remain
OFF and both owned NFS views remain read-only. Matching source7 protected
authority, installed recovery, writer/restart/rollback and later release/production
acceptance are still pending. Production remains unchanged.


Source7 genuine helper proposal and matching bootstrap ACTUAL PASS. Official
prepare-host-helper.py produces candidate0bed55370e86ad816efa737d28c40854f028f3a556878cb05a114554e02625b9
in1.106s from selected cut861/fullsnapshot155f under offline original1706EX;
no stderr. Protected publication1.262s retains original source6 index/policy
inodes61480742/61480743 whole, publishes index inode61580605/root0644 and
policy inode61580606/root0600, matching conf SIDs. New all-six-false policy
7e1e142a7798b601fd0ee455bd9171aa6fe9c4e56f1a5cb66d416aff63b0f99e.
No CIL/module/SELinux receipt or key/credential/store effect.

Fresh metadata preflight1.403s verifies all11 retained stopped CIDs, six image
identities, nine original bindings, masks, exact authority, engine coordination
SIDs and both NFS-ro views. Receipt49d3d7967e36bbfb3be7947c30fe71305244492ef7eeac40230fa7e43c5c5050.
Only remaining prerequisite is the separately reviewed ordered startup. Both
manager reloads and ONLY helper NotifyREADY pass3.518s with original hardening
and actual helper_t/caps0xc0, pid43210/birth4505098. Worker-only start passes
34.779s: NotifyREADY conmon43374, independent payload43377/birth4509904,
CIDd4678299ba1b79f82e12e268fe528c711dd0685a91157b7162b34a7ef3250272,
container_t:s0:c450,c663, mapped983, zero capabilities, no-IP/offline and all
credential masks. API-only start passes9.096s: payload43524/birth4511411,
CIDb79059fed09be4264a3f5737b3081f755f994da5ac06492411b80359cc84e6a0,
container_t:s0:c37,c877, descriptor-bound listener joins original parent27:1330;
actual Type=exec foregroundPodman is independently qualified. Caddy-only start
passes1.885s: payload43917/birth4513968,
CID7f00d6b9bf035714b2f752a311f7c28001ab29910eb04db5a4e3e2d1ba30f4f7,
container_t:s0:c412,c959, original TLS secret identities and no archive mount.
Original locks, stores, credentials and nine-entry marker remain unchanged.
Bridge/guard/targets/sockets remain OFF, schedules disabled/legacy masks intact;
these are explicit current-boot starts, not unattended boot acceptance. Strict
TLS/UI/API-worker reads and browser recovery remain pending. Production unchanged.


Source7 installed strict TLS/UI/API-worker reads ACTUAL PASS9.257s: all ten
authenticated GETs return200 across root and /management, exact selected UI
shell/module bytes and source861/UIc4, actual API-container SDK Argon2 proof
using only the positively owned fixture donor over stdin, verified CA/IP/leaf,
and real API-origin worker PROBE. Original histories and private metadata
unchanged. This closes guarded installed read/startup identity only.

Source7 original-browser followon1 ACTUAL FAIL44.766s; preserve original
report6b567a820b71fcc08bf2ea71b51bb0939df739980867456a294823b2a4ff6bfc,
all stdout/stderr and original record85ccd17367bd4ff5ad949f79cc0ee108/key
b5e37d8e-4932-4730-bc78-f5733d9c26d0. Ordinary automatic GET200unknown
correctly retains browser missing/Needs review, originalAuthority and all handles
across actual API restart df457aba98634180a2e038cfe935606e. Deliberate first
retirement POST returns503HFAPI015; no job POST, remaining five cases unexecuted.
Fresh helper journal advances past the repaired notify-worker predicate and
reports PermissionError13 at _intent_executors line2543: the original inert
cohort scan opens an OS executable solely for an unused body read. The five
fixed process executable metadata identities are captured separately; no
permission expansion, body grant, replay or success claim follows. Named high-
effort repair resumes against the original bounded closed cohort, retaining
process/parent/group/argv/domain/birth joins. Source7 gate remains historical
green for its exact inputs; the newly changed source will require a fresh gate.

Independent failed-browser closure ACTUAL PASS: CID
deeb10c93adde146f752449f2b877d7a09a623d3abfc359fda16963dfee53b13,
exit1/PID0/noOOM, no remaining cgroups, contexts/browsers closed. Receipt
1ce54402ee176d641b2f8f9d1f7817cd8a3d588ae86c8ac5a93147174df791fa.
Original raw export94de and nine-entry marker27c3 remain byte-identical.

Fresh source7 critical-state backup/tar compare passes1.425s before the next
reviewed drain, root0600/4843520B/inode111224251, covering19 roots including
all original plus source7 failed handles/reports, current prefix/authority/code,
stores/backups/secrets/both PHC records. Original global/companion/store/secret
guards release before drain. No private body digests, permission reset, archive
access or production effect. The prepared source7 Hub-only lostack scripts are
unexecuted and require a successful original-recovery receipt; this failed
followon cannot qualify that prerequisite. No automatic grant or browser replay.


Actual graceful source7 retention-drain passes8.285s after the fresh19-root
backup. Exact CIDs retained as web033-source7-online-caddy/api/worker before
normal stop--time -1; proxy first, then API with worker/helper available, then
worker/helper. All three exit0/noOOM, original pidfds and whole service/libpod
cgroups close, original five inert983 actors remain. All14 core CIDs and six
images/tags remain; no rm/restart/force kill. Original stores/bytes compared in
RAM and original locks/PHCs/credentials/mounts/masks preserved. Backup receipt
82cebeb1791f65019fc67f05119b47af12e7d170a7d0bf9e6595b23657f24aa6;
drain a55de6f7673597a8f2bbe6b108c91eb38876082be329d3cd2660f742e03739f4.

Post-drain local-state backup/tar compare passes0.933s, root0600/81920B/
inode11761271. Caddy/HF/cache/secrets/stores preserved; original old flat
sockets remain unbound and selected sockets are removed only by normal
application cleanup. All six guards release. All fixture application/helper
roles are now OFF while source7 guarded selection and all-six-false authority
remain selected, Enforcing/NFS-ro. Production host fresh read confirms boot
45d3ce1d-735b-45cc-b731-e2f39860d65f, Enforcing and original NAS NFS-ro
nosuid/nodev/noexec/nconnect4; no production mutation.


Source8 prerequisite refinement from ACTUAL loaded policy: guest sesearch is
unavailable, so exact public kernel binary4e6b09f1ca5ce42dcc9945c259823506f7dea2694501de36d914b251b91edfda
(3465352B) and331 current guest booleans are read-only captured locally. Host
setools queries that exact binary, not an AV-only reconstruction: helper file
rights for init_exec_t and dbusd_exec_t are both empty, including getattr.
Receipt rootless7-inert-executable-actual-TE-rights1.json preserves those facts.
An O_PATH-only implementation still needs fstat/getattr, so the earlier intent
to keep CIL completely unchanged is insufficient. Qualify only these two
file(getattr) forms alongside closed OS-path O_PATH metadata checks; no open,
read, map, execution, process-control or generic executable allowance. All
neverallows, conmon getattr-only and payload denials remain binding. Actual
metadata and policy checks must precede any claimed installed success.


Source8 technical inputs FINAL FROZEN: ten-path receipt
68afa0f58aa7e192497996d0be5f5f4dc15198e32096120922bdd4658ac74c5c,
sourcepeer c50770f3e25c872b90bf7ff14d4cda498c6a78976ca0915f1b7d674a0078bc7a,
CILd07793d286ec58c78eb8d09986e8b52d4e5724ab9f79c25fc6b4aecac56837fc.
Earlier freeze5a2238 is preserved/superseded. Actual-shape red regressions
reproduce the unused body-read refusal; only five existing fixed OS executables
may use protected no-follow O_PATH metadata, retained ancestor/leaf identities,
full path rejoin and charged before/after kernel executable-inode joins.
Unknown paths, mismatches/races and failed observations refuse; exact original
process/argv/label/parent/cgroup/credential/birth checks and aggregate budgets
remain. No OS executable body read, generic selector or privilege bypass.
Final471 focused tests pass4.85s, including ten kernel-before/after mismatch
cases; Ruff/format3files, focused Pyrefly0errors and diff checks pass.
Original intent-lock regression remains byte-identical to source7.

Actual loaded policy4e6b shows no helper file rights for init_exec_t/dbusd_exec_t;
CIL adds exactly their two file(getattr) forms. All38neverallow forms and conmon
getattr-only remain unchanged. No body open/read/map/execute or process/control
right is added. Private copied source7/source8 strict compiles BOTH FAIL with
the same38 normalized standing failures (owned paths/helper source offsets only
normalized), logs retained, no strict-pass or runtime inference. Separate AV-only
checks are comparison evidence only and their binaries are NEVER installed.
ADR150/164, INV020/023 and recovery/host/security contracts reviewed/amended
first; no new architectural decision/public/durable format/dependency/unit or
capability. Root alone owns fresh strict gate8 and actual matching installation;
all source7 failures/handles/marker9 and original states/predecessors remain.


Source8 gate8 deliberately INTERRUPTED, not passed: during the frozen run a
read-only target metadata qualification establishes that the actual standard
/usr/lib/systemd/systemd-executor is1413592B, regular root0:0/0755/nlink1.
The new metadata-only helper retained the obsolete unused body-read MAX_READ
1MiB ceiling, which would still refuse this legitimate fixed actor after the
getattr repair. Preserve the original metadata check/refusal and all prior
freeze receipts. Remove only that body-byte ceiling from metadata validation;
retain positive/coherent stat size and closed paths/root ownership/mode/nlink/
executable, parent/leaf/kernel joins, deadline and file budget. No body is read
and charged read bytes remain zero; no read budget increase or larger arbitrary
cap is introduced. Exact actual1413592B regression is required.

To avoid spending the remainder of a full gate on a known target-conformance
defect, root sent ONE SIGINT through a freshly joined pidfd to exact owned
pytest178321/birth4773067. Ancestry binds to gate8 runner178237 in its private
empty-NFS-shadow namespace4026532694/UID1000. Gate/shadow exit1 after542.509s,
partial results and fixture-unwind KeyError retained; no gatepass is inferred.
All1283 source names/bytes remain unchanged through interruption. Independent
whole-namespace process inspection confirms ZERO remaining actors before source
edits resume, receipt gate8-interrupted-closure.json. No force kill, testrestart,
application/VM/production effect or archive access. Focused minimal repair and a
fresh full strict gate9 on final bytes are now required before source8 builds.

Copied source7/source8 policy checks are unaffected by the size-only repair:
26 AV-only comparisons pass at recorded actual guest331booleans, receipt
2d7de0dc8fddda3aca7d102bbb39c7feaacb35cacff380f83e0dcfce4851cb54.
Only init_exec_t/dbusd_exec_t file getattr is added; payload denials, conmon
getattr-only, capabilities and manager control remain unchanged. Both strict
copied compiles preserve identical38 standing failures, never called passed.
No AV-only binary is installed. Source8 policy/peer handoff procedures have
separate static review and strengthen same-input-set/full-metadata joins; all
future genuine source8 build/stage/switch/labels inputs remain pending.


Source8 FINAL freeze3 supersedes freezes1/2 after gate8 whole-namespace closure.
Exact target1413592B regression fails before removal of the obsolete metadata
byte ceiling and passes afterward. Final471 focused tests pass4.07s, Ruffcheck/
format3files/focused Pyrefly0errors/diffcheck pass. Only peer source and its
existing regression test differ from freeze2; all other eight paths, CILd077
and its policy comparisons are unchanged. Original intent-lock regression is
byte-identical to source7. No contract change was needed: contracts already
require metadata-only proof and aggregate read budget, not an executable body
size ceiling. Positive/coherent stat size, exact protected five paths, root/
mode/nlink/executable checks, parent/leaf/kernel inode and process joins, file/
deadline budgets and zero executable read bytes remain. No larger arbitrary
limit, read-budget increase, selector, capability or body-read allowance.

Final freeze3 receipt86425064c4721fdeee27e0c45bf35ff14882a067d3a2f5ed294b2f21ec54d44a;
peer36078a418372bfe0d3a4b5116c3e18ab8bda6f9e9e3534d43667a629798cb769;
test executorsbb8b089cf7ebed479f420a1e6ba6953789828368390625ee6d9e69d57e974757.
Fresh strictgate9 is required on these final bytes. No source8 artifact, policy
load, startup, browser review or production effect has occurred. Owned fixture
remains source7 selected/all-six-false, apps/helper OFF, original states and
predecessors preserved, Enforcing/NFS-ro.


Source8 final strictgate9 ACTUAL PASS1470.165s (shadow1470.421s):
rtk scripts/check.sh --require-web, 9874 backend passed/52 deselected in1163.28s,
package build plus locked base/server/server+MCP wheel installations/import/help/
version,179 generated transport definitions,23 sandbox/19 functional metadata,
3809 unit/4169 combined component tests and16 built sandboxed browser checks,
no required skips. Actual200% zoom/320CSS keyboard/scroll/pagination and real
HTTP/API React source fixture pass. All1283 source names/bytes remain unchanged.
Resultbb1b14c38117f4f04d5f59d0055801a0aebe26717180a64bc632e2840c22988d,
raw log5800673b1a25d13fd752f2d84e78f8f0e14a63e81bb92ee95da58dd4fe4c3348.
Gate8 remains deliberately interrupted/failed; gate9 alone qualifies these
final source8 technical bytes. No repeat full gate without another technical
change. Post-gate edits are factual task/current evidence only and require the
existing scoped documentation checks before a clean detached build cut.

Installed/Caddy/production evidence is separate. Matching source8 clean build,
actual two-getattr module/receipt and peer/authority handoff, original-browser
retirement, writer/restart/rollback and later release/production packages remain
pending. Source7 fixture apps/helper remain OFF with all originals preserved;
no source8 policy/runtime or production effect is inferred from this pass.


Source8 immutable cut/build/guarded handoff ACTUAL. Scoped post-gate docs9
passes7.968s after factual task/current edits only. Clean detached cut
817629a9910b4d4ee730ef6a7c01410c2d70f935, tree2bd0399383266c22dfd5a160d65ac3df38be619d;
main7894540 unchanged, both original regressions/draft retained. Locked source7
tool donors cloned exactly, only new editable project path rebound. Native
bundle reproducible build10.196s: index445a9a956c5400319ee8287119061d34e85e5b17d566c1c5aff77b6c58074d41,
build evidence12434e44652c9149006d2834abe8c9d680b8be7fbfb78930df99397f46dc7efc,
full snapshotd044e6b095643cbf9d4f4996fe5d44b5c3e7cc5ed06f80a58d3df4a9f3ff7889,
UI9b2912c65852f00545ac01cca870eced8a2fdab3b7e69a2d7371420bba3bf1f3,
wheel5545dbbd3e43431283fe57bc04365fa39d376dc4179d57aa275a45989f6dfbec.
App image build22.216s:42aada3280a7e064e2d099f168b6d38371d1b18387a7bdbe40fb491322431767,
local tag localhost/hfcache:web033-source8-817629a9; no publication.

First strict bundle receiver refuses the sole source/CLAUDE.md -> AGENTS.md
link before verification, preserving original transfer failure. Whole24-node
partial copy retained by same-FS nonreplacement rename at
/root/web033-artifacts8-transfer1-refused, root inode61708337, no deletion.
A newly reviewed receiver permits only that exact internal link; fresh1398-
member transfer then official verify-native passes14.957s at
/root/web033-artifacts8. Original failed receiver/partial remain. Genuine
proposal tool is source/scripts/prepare-host-helper.py inside that bundle.

Local OCI export3.577s:66336256B/0e01a8255537304cda75cf2d76375ceff8a91ddba10de19124981bed894546cd;
all local image/tag metadata unchanged. Exact OCI and35 sibling-input members
transfer; guarded manifest a73ae299714cbf40f987f7e284480ae87ff5c1c1211ec0614df386c44989167b,
manual a6f08f7bf87255a085e8ef9bbe527bb2170cff20a198ac551685f3aca9650361.
Official UID983 stdin import8.451s preserves all14 stopped CIDs and six old
images/tags; only matching seventh image added. Receipt
623f6563d27fef46cec2616ae9382d5bfb659323fd2ef5601048e9baa6caa413.

Whole117-node source7 prefix/current80332352 retained at
/opt/hfcache-web033-rootless-source7-retained by RNR under fresh original1706EX,
all bytes/inodes/attributes except explained root rename ctime preserved.
Receipt ed3f2deb995df03d59004879f1895a3891989f919d3219ea326edd2f3858176b.
Both official stages pass2.840s; guarded index
d94fc8a549b11343766af2a8ff2b5c709a85c8eb16e8b872c03dd3ca490ef491,
runtime2aedd4b6432be18f647c489ca21776c41473cf2ecc0089a79db553fc5aa04fb4;
manual index23ccbc3e1e078ffd12ac11fe62ef286993f9e91d3145ad77df448de9636dff45,
runtimee181a06ac185046be64b59919bc803cffdfe2af14a900d459a02f56eba3b36a6.
Existing fcontexts apply to18 exact new public leaves, no new rule/module/boolean
or retained-tree relabel. Labels3.705s receipt121436f52e67d15447921c4601b985421a70a4972edb4a13bd2dc5dd50a2fa1c.
Official guarded switch1.391s selects current inode44894396; receipt
41a9d70622b9efd568503b5ae09cff69fbcd7d53b901a5a62ba583e751ee0efe.
All roles remain OFF and both owned NFS aliases RO.

Root-private reviewed inputsf212c98627acb07dc4e375594969ae0dcb5d74dc2e923d53ab4108c22b999862
bind the actual cut/build/source snapshot and four exact protected stage/switch/
label/retention receipts. Independent static handoff review adds same-input-SHA/
source joins across policy and peer steps plus full CIL/receipt metadata joins;
all drafts remain. Protected policy/configuration backup/tar compare and original
EX precede one actual source8 module load. Policy handoff11.561s passes, old
CIL/receipt whole inodes retained; only module d077 replaces726, version1 receipt
tracks actual kernel5ec447b9bacf436e58d3cf514efb19284be8cf980375ea7fbbcf5284b0dc6d10
and receipt6ba51ecfa5363f1c973804c8c21e8e3382f1d759abcf3ea2b67f2e92ea39322d.
Canonical CIL inode80332354 and receipt61556809/root0644 preserve expected SIDs.
Policy receiptfd9c549912937d4b9d7e97394befacc6dfb45d99f9176017ff2520700240f85f.
Booleans, fcontexts, other modules/code/units, stores/bytes/credentials, original
locks, marker9 and source7 authority remain unchanged; no engine/start/archive
effect. Peer-only handoff3.406s then preserves old4cda code whole and publishes
36078a41, joins same inputs and exact new CIL/receipt facts. Original index/policy
remain unchanged until the next genuine bootstrap step.

Official source8 helper proposal1.126s passes with candidate
aa992ecd6ce13105b8b172dc85fc78da0971c5fbc41d9127229d1836c14b9130.
Its copied scope prose retains the source7 label; argv, source.parent_commit817,
full snapshotd044, selected app42aa/runtime2aedd and peer/module/receipt bindings
are explicitly checked as source8. Preserve that original receipt, no rerun or
authority inference from prose. Protected bootstrap1.277s retains source7 index/
policy inodes61580605/61580606 whole, installs source8 index inode61556810/root0644
and all-six-false policy inode61556811/root0600, policy
e963e66bd74bd9236d7635b56c0db11df45c1455293738c6a53b09c6965b3846.
All original controls/credentials/stores/locks remain unchanged. Startup, fixed
actual browser retirement, writer/restart/rollback and later production packages
remain pending. Production unchanged; no archive write or recovery success is
inferred from build/stage/authority qualification.


Source8 installed startup/strict TLS ACTUAL PASS. Fresh preflight1.393s verifies
all14 prior stopped CIDs/seven images, original bindings/masks/engine SIDs and
both NFS-ro views, receipt76a7906f891e6eff9ff5e34d1ac59439ab8cf24e743acd27ff5dc6b92c4efa0f.
Helper-only start3.578s: pid48192/birth4897399/helper_t, unchanged caps0xc0/NNP/
hardening and matching aa992/e963 binding. Worker-only start47.184s: actual
notify monitor48387, payload48390/birth4906954,
CID7227c27f5671a21e8b60ad9c46d80f51566ae2a7ba2ed50ae99663ae0917992a,
container_t:s0:c248,c756, mapped983/cap0/offline/no-network/credential masks.
API-only start9.020s: pid48535/birth4910837,
CID1e3377312f23cd9084aae184740ed813d1a1e11af30b7686d9dd37e4fcc67390,
container_t:s0:c60,c728; actual Type=exec foreground Podman and held-parent
Unix listener independently joined. Caddy-only start1.809s: pid48929/birth4916298,
CIDa0237e60d4e9dbbf2f37fa83812caf45c44789ddb7e67c54a63beef566bd965a,
container_t:s0:c180,c747/TCP8443/original TLS secrets/no archive bind.
Ten real authenticated strict-TLS root/management bootstrap/version/readiness/UI
shell/module GETs pass200 in9.339s, source817/UI9b exact, original CA/IP/leaf,
actual API-container Argon2 SDK using known owned-fixture donor stdin/RAM, and
real API-origin worker PROBE. All original store bytes/private metadata remain.

Source8 first original-browser followon ACTUAL FAIL43.357s. First ordinary
GET200unknown preserves missing/Needs review, original85ccd/b5e handles and
authority across new API instance0a01968aae2b452792ae8d2ec3e7f904. The ONE
deliberate retirement POST again returns503HFAPI015, no job POST; remaining
five cases unexecuted. Source8 helper journal now advances beyond file-body/
size checks and refuses initial os.readlink at _intent_executors line2608.
Independent UID983 probe reads manager/catatonit/broker executable links, but
stock sd-pam21207 alone returns EACCES. Preserve failure report
3c56997223fc5d4c962ea87020c16fb9c35d11b956c6e1c4bda65320641638cd.
Independent browser closure passes: exact CID
0448aba46edd38f02b89802dea92335a26837e652344281b144177c242df7045,
exit1/PID0/noOOM/no remaining group, all contexts/browsers closed; receipt
8e58d9020a7b13a54c7d005302097862e71ea6eed4f177cee5a862dd6bc0d2c2.
Marker9/27c3 and original raw94de remain byte-identical; no recovery success.

Finite actual public identity facts are captured as UID983 before source9
repair: PAM pid21207/start2687098/direct parent manager21205/start2687095;
argv/name(sd-pam), exact system_u:system_r:init_t:s0, four UID/GID fields983,
no groups/tracer, zero Eff/Prm/Inh/Amb, initial UID/GID maps0:0:4294967295,
NSpid/Pid/Tgid21207, sleeping/no pending signals. SigBlk is ZERO: never infer
a blocked-SIGTERM/sigwait proof. Proc directory remains983-owned; exe SYMLINK
is0:0-owned and not readable/followable by the service account. Fixed protected
user@983.service has Type notify-reload, User983/PAMName systemd-user,
Invocation4f79feffb9394f59b53dc91ddc747450, canonical root0644 vendor fragment
and10-login-barrier.conf dropin. Installed systemd257-34.el10/kernel6.12.0-275.
These facts support a distinct closed trusted-PAM lineage proof, not an image
claim or permission-error bypass; new caps, ptrace, PAM/process/policy changes
are forbidden. Source9 contract-first high-effort repair and a finite actual
confined read-only component check are pending; no archive or production effect.

Fresh21-root critical backup/tar compare passes1.462s, root0600/4904960B/
inode29727450, including source8 original failure/handles and all predecessors.
Receipt4cfa29cfce862eaa6702e277887a04e9497c13ec42cee451013276486ffbfae4.
Actual graceful retention-drain then passes8.905s, exact live source8 CIDs
renamed once to web033-source8-online-{caddy,api,worker} before stop--time -1;
proxy, API with worker/helper available, worker, helper. All exit0/noOOM and
pidfd/full service+libpod cgroup closure, original five inert983 actors remain.
All17 stopped core CIDs/seven images/tags retained, all store bytes compared in
RAM, original locks/credentials/history/mounts/masks exact. Drain receipt
3376579319dfafef49567df62280e8a4818b57b4ad49838fb32432d66a3fd1fe.
Post-drain local-state tar/compare also passes0.933s, root0600/81920B/inode
80392313; old flat sockets remain unbound/preserved, selected sockets clean up
only through normal application exit, six guards release. Source8 selected
current44894396/indexaa992/policye963 all false/CILd077/kernel5ec/receipt6ba
remain; ALL app/helper roles now OFF. Source8 Hub-only lostack preparations
remain unexecuted and their required successful15-entry recovery receipt does
not exist. Production remains unchanged, Enforcing/NFS-ro.


Source9 focused candidate e06a7ba758c86ca91e0ae75726d61f85bc06c6cb6452ca76649f8304a8191fb6
passes505 focused checks, Ruff/format/types; eight-path focused-ready receipt
80740453200cc6f8efc604f1f34ad0fb558d21a7f5c0fa19d99ba41f7641715b.
This introduces a separately typed closed trusted-PAM lineage/metadata branch,
without claiming unreadable executable-image authentication. No CIL/capability/
NNP or canonical installed authority changes accompany this candidate.
Actual finite component probes are not installed retirement acceptance. Preserve
component1 (manager CLI refusal after harness UID drop without exec), component2
(harness incorrectly lstat of root-owned /proc/self symlink), and component3
(correct UID-before-exec process-directory proof, then fixed auxiliary CLI
nonzero before PAM call). Independent closure receipts6448b1d2/ac079ec7/7ca49f75
prove each failed unit MainPID0/ControlPID0/empty cgroup, original five inert
actors, exact original fixed/store metadata and unchanged Enforcing kernel.
Component3 actual identity53048/start5127948/helper_t/UIDGID983/no groups/
zero EffPrmInhAmb/NNP1 passes; postfailure exact system-manager GET passes, so
component4 captures both fixed manager/broker command diagnostics. No product
failure is inferred from a harness failure; no probe failure is counted passed.
All failed code, units and results remain. Canonical roles remain OFF and
source8 guarded authority, original handles/marker9 and production unchanged.


Source9 actual finite confined PAM component5 PASSES4.906s. Component4 isolates
broker CLI EPERM to the probe's erroneous ProtectHome=yes masking /run/user;
the packaged helper already uses ReadOnlyPaths=/home /root. Component5 matches
those existing paths, preserving canonical hardening and all other probe masks;
no product policy/capability change. Actual helper_t53599/start5141016 runs
fresh exec as four UID/GID983/no groups/zero EffPrmInhAmb/NNP1, bounded0xc0.
Both fixed manager/broker reads pass. Actual _intent_pam twice joins protected
manager21205/start2687095/Invocation4f79feff, PAM21207/start2687098/init_t,
exact direct parent/credentials/initial maps/status and nofollow directory/exe
SYMLINK metadata. Requeried auxiliary and deployment are identical;70 charged
files/44006B. No executable image authentication is claimed. Exact probe pidfd/
full cgroup close naturally, original1706EX releases, original five inert actors,
all fixed/store metadata/marker9/kernel5ec/Enforcing remain exact. Original
failed components1-4/code/units remain; component4 independent closure0b01aed1.
Actual component receipt /root/web033-pam9-component5/result.json and host
/var/tmp/web-033-fixture/pam9-component5.json retain full proof. Canonical peer
remains source8/36078, current/index/policy unchanged and all app/helper roles
OFF. This qualifies the bounded new PAM proof, not installed retirement, writer
acceptance or production effects. Fresh strictgate10 is next, with eight technical
paths verified byte-identical to focused-ready80740453 and CILd077 unchanged.


Source9 strictgate10 ACTUAL PASS: all9908backend/52deselected in1191.69s,
locked base/server/server+MCP wheel install/import/help/version,179wire,
required functional metadata19/no required skips, frontend unit/combined,
16built sandbox browser, actual200%zoom/320CSS keyboard/scroll and real API
React read checks. Whole gate1504.926s; private empty read-only NAS shadow,
loginUID1000/nice10. Frozen1283 source names/bytes all unchanged. Result
web033-gate10-result.json and raw log retain exact authorities; no installed
retirement/writer/production acceptance is inferred. Component5 protected
receipt625424636d692a3534036fea0965395565cff80802ea8ed3126effc4409e0428.
High-effort peer-only handoff static review is ready, draft9bbe57f6: independently
joins retained source8 current44894396/source817/artifact/runtime, source9
fresh stage/switch/inputs and actual component5; fd9 is explicitly historical
unchanged source8 module qualification, not a new reload. Source9 clean cut/build/
stage/current/authority/startup remain pending. Post-gate changes are factual task/
current only, checked separately before clean immutable fixture assembly.


Source9 matching clean fixture cut/build/install/startup/TLS ACTUAL PASS.
Post-gate factual docs10 passes8.121s; clean detached7edeece9437cd21bdda4cedc84f5144efe43b8e3
(tree2919bb74) retains main7894540 and every source8 donor. All1283 gated
technical bytes remain; only task/current factual evidence follows gate10.
Locked tools cloned with donor inventories unchanged (7692/33/14191 entries).
Native reproducible build10.672s: index27d043adaad27e73690ca06802f04ab60ee58a3dc89dfac64b9233c18f182183,
build-evidence0b42219b950b84c79f814f04ffc5359087e1e1aee36c62895b2eb34902304530,
FULL snapshot9ab8f2e65b31a0d96f7c0ab3e582dac258e33c90f1a10984b75de372f97a162a,
UI09d0c0314b9732118acc4649df772bf4f2e7b9e9cbaf340021e2edbc631f6b74,
wheel dc1eefbbefe5e97b5e03f020912db5898d4223f9a760da1f867f918a4c23ebe0.
Matching app build24.619s: sha256:0639bda4111378de037ad832c6dd49cfe4e8b512654a95b1c1c424ac3c0b601f,
unchanged locked dependency closure/Caddy/actual JS2409dca5. Exact bundle transfer
7.523s and official verify-native pass, sole source/CLAUDE.md->AGENTS.md internal
link qualified; source8 refused transfer and all predecessors remain. OCI export
66336256B/fd7defef30e9d8985cafa5980189300e31f25e68da483ea016c34bac02d39698,
3.544s, all local image metadata unchanged; root-private exact transfer succeeds.
Guarded/manual manifests1c7f2c20/c6a6700d capture /management before hashing.

Guest image import9.188s preserves17 stopped CIDs/seven prior images (now eight),
original controls/stores/credentials; receipt2cee19d3bd7c0b64017d05e664161ef83a2d725aa0deb656cdce985f34fcd055.
Whole source8 prefix retention0.506s preserves117 nodes/current44894396 at
/opt/hfcache-web033-rootless-source8-retained; receipt13b0f2b48269f9e7e3cd8e7f95f7f214bd98b9863492ca43893dc5d2760b7b41.
Both official stages2.902s, original noncreating EX acquired independently:
guarded index93d7ecd09de065b00e226d2b6efd0ada16756cf3f94e53aa20928e458f0ccc3b/runtime8312f02681479cb98f7a3cfc54042df37b6bf372edf22c3249365a528a90e2a9;
manual index79a0be5eea15ae4b014a46efcbb9e108d1d34e9a900a9f05e44332cf92a17c8c/runtime8a67f823545febbd389255bd11a9b731b2212196d5a55c13f4076437e5769ea1.
Existing18 public label matches only3.549s, receipt72f9f47c; one official guarded
switch1.374s/current128213298/receipt6e5698f2, all roles OFF/NFS-ro.
Fresh root-reviewed inputsc73ec5da45790fb5f3c8bd8bc99bc5ff6fd09126871ca53a35e1194825f4f73a
bind source/build/full snapshot and actual four stage/switch/labels/retention receipts.

Reviewed peer-only handoff3.516s retains whole source8 peer36078/inode80249916,
publishes e06a7/inode80258433, protected fresh backup/tar compare and original EX.
Independent retained source8 selector/release/component5/source9 inputs rejoin;
CILd077/kernel5ec/SELinuxreceipt6ba remain EXACT, no module/receipt replacement.
Peer receiptefaccf9e672ae41c4f185b85833278c6aadb10d8a62a1efc428fb85c0a19830c.
Genuine official source9 proposal1.099s binds7ed/9ab/0639/runtime8312, candidate
5dca79c9bdb6a933aa3e690fd3e2ee2858d0a19d324660b956d4aa0a19e3aa9e.
Bootstrap1.272s retains aa992/e963 original inodes61556810/61556811 whole,
new index61660759/root0644 and six-false policy61660760/root0600/SIDs exact;
policy443a2aac42605d108cc89cba75dd811715db6801ce85f984e9eff33f3f5386f3,
bootstrap receiptc0c3cda69692c71d28af0b86951b69c274863325935cb58c27f5b345e54b6dd1.

Preflight1.388s passes all17 stopped CIDs/eight images, original nine aliases/
masks/locks/credentials/engine SIDs and both NFS-ro views; receipt2fb4a6b0.
Only expected startup steps remain. Helper3.304s NotifyREADY55267/start5344593,
helper_t/caps0xc0/NNP/original hardening. Worker34.108s payload55468/start5353073,
actual notify/conmon/foreground Podman/private network/cap0 proof passes.
API8.993s descriptor-bound listener and foreground/conmon/payload proof passes;
Caddy1.857s original TLS secrets and TCP8443/confinement proof passes.
Ten actual authenticated strict-TLS GETs9.381s pass200/source7ed/UI09d/root+
management/exact JS and real API-origin private worker PROBE. Fixture Basic is
verified with actual selected API Argon2 SDK via known donor stdin/RAM only;
all original store bytes/private metadata remain. TLS receipt
9f4cd7850d6c811087b70e7043c9f5291bb91cafda53557bcc3c02023751eaf3.

Source9 original-request six-case installed browser followon1 is LIVE. Its driver
5c09e394 and launcher8b64310c differ only in new source/UI/output/selection pins;
old driver, original raw94de/85ccd/b5e handles and prior failure closure8e58 remain.
No browser recovery success, marker15, Hub pilot, writer/restart/rollback or
production result is claimed before actual completion. Production unchanged.


Source9 original browser followon1 ACTUAL FAIL48.339s; first ordinary GET200unknown
again preserves85ccd/b5e original handles/authority/state missing under new
APIinstance8c4aecd243c74035b6156df06e076335. ONE deliberate own-key retirement
POST503HFAPI015, zero jobPOST, remaining five cases unexecuted. Report
 d9f74aee0d4768c92be89c90a5bf47febad3576dd95ff3ab8dfdf9046167e7c9.
Helper now passes the PAM branch and reaches _intent_executors2758: typed
auxiliary classification returns None. Existing public manager/broker reads and
all five actor facts are captured; fixed pause.pid names21279/start2712684,
catatonit -P/protected fixed executable/container_runtime_t/user namespace
4026532303/maps[[0,983,1],[1,165536,65536]], but its parent is PID1, not manager
21205. This already-authenticated detached keeper is legitimately reparented;
other manager/broker-launch/broker classifications pass. No broad orphan skip,
new capability/policy or historical nonexecution inference is authorized.
Public facts2 retained at source9-inert-classifier-public-facts2.json; facts1
refused a PAM namespace-link diagnostic not used by the PAM proof and remains
failed/preserved. Source10 narrow contract-first keeper-parent repair is next.

Independent failed-browser closure PASSES: CID
475f669d6f0dbf020bce32f1ebca8f4b7629f6a024d0a18f649c80cdc6edcf62,
exit1/PID0/noOOM/empty cgroup, contexts/browsers closed. Original raw94de,
all fixed/private/store metadata and marker9/27c3 remain exact; closure
905afbe72f78a1cdbfdf8548597d7904cff04a6fdab45d429f8409f151f3cceb.
No recovery success or successful15-entry prerequisite exists; all Hub lostack
preparations remain unexecuted and forbidden until that actual prerequisite.

Fresh23-root coordinated critical backup/tar compare PASSES1.425s, root0600,
4966400B/inode29938932; receiptc012c26e0a6583c9d04d79afb1dd48b7c2ff71ea3ed2f01020e7befe7d504965.
All backup guards release before actual graceful retention-drain9.493s:
source9 CIDs renamed once web033-source9-online-{caddy,api,worker} then normal
stop--time -1; proxy, API with worker/helper available, worker, helper. All
payload/foreground/conmon/pasta pidfds and full service/libpod groups close;
20 stopped core CIDs/eight images/tags retained and original five inert983 actors
remain. Receipt854ebd8509fc53918560e85795b8fddfe238f16803d092ea22561b4911ce0a3f.
Original store bytes compared only in RAM, all fixed/runtime/secret locks,
credentials/history/marker9/NFS-ro/Enforcing exact. Postdrain private local tar/
compare also passes0.917s; old flat sockets remain preserved/unbound, selected
sockets clean up only by normal app exit, all six guards release. ALL canonical
app/helper roles now OFF. Source9 guarded current128213298/index5dca/policy443a
allfalse/peer e06/CILd077/kernel5ec/receipt6ba remain. Production unchanged.


Source10 finite follow-up for the reproduced source9 keeper refusal:

| Changed requirement | Smallest meaningful check | Gate and result |
| --- | --- | --- |
| Already-authenticated detached rootless keeper may have PID1 or verified-manager parent; retain prepared UID/GID/maps and all fixed image/inode/domain/PID/birth proofs | Actual21279/parent1 red regression; both exact allowed parents and mismatched identity/owner/maps/executable/domain refusals; one confined fixed-five-inert metadata component using genuine _engine_prepare and fresh auxiliary facts | Focused checks/component pending; fresh strictgate11 and matching installed original recovery remain required |

The intended source10 peer candidate is74b118a8822b5272706ebb8825423ba72a9da916c0103b81cd910699e0bb749c;
root holds it for the finite component, with no canonical source10 publication.
No new generic orphan allowlist, process skip, policy/unit/capability/syscall/
budget/dependency/durable-format change follows. Postdrain local backup receipt
2f2eecd41054904242b3fca5075ee4af36fdf918ceddd62613d17de2b74e3058,
root0600/81920B/inode80459041, complements the critical backup and full drain.


Source10 candidate peer74b passes519 focused checks4.26s; adding the observed
broker process-metadata policy regression brings the current focused set to520
passing4.34s, lint/format/types clean. CIL e1e8632a4db852b2cd3fb34327c263fa48ae0591270fecc0f9a605ce53e89ac0
is an INTERMEDIATE uninstalled candidate adding only helper->unconfined_dbusd_t
process(getattr). It is not the final technical freeze or actual policy.

Before another full gate/build, finite actual five-inert component1 FAILS4.770s
under helper_t59284/start5479288, fresh UID/GID983/no groups/zero E/P/I/A,
Bnd0xc0/NNP1/Seccomp2+27filters. Genuine _engine_prepare passes; the new keeper
branch is reached in the probe. Later broker attr/current read is denied by the
existing d077/5ec policy: audit22921 process{getattr}, targetunconfined_dbusd_t.
The component does not count as qualification. Independent closure5656756192cdb7927789a0785c691461f7a1a8c879198012efa6afe48f8232eb
proves MainPID0/ControlPID0/empty cgroup, original13 fixed metadata (including
API runtime1334/worker instance18402599), stores/cohort/kernel unchanged.
All failed code/unit/journal evidence remains; no canonical source10 publication.

One fixed-two-broker readlink/follow-stat diagnostic then COMPLETES4.806s with
qualification explicitly FALSE. Actual helper_t59610/start5541138 has the same
unprivileged/no-group/zero E/P/I/A/Bnd0xc0/NNP/seccomp envelope. Both fixed
brokers21288/21289 readlink and follow-stat return EACCES13; audit23093-23096
identifies ONLY lnk_file{read} denied under unconfined_dbusd_t. No link getattr
right is inferred. Receiptb98fc1c472fec35cb524b62524c90e0ba212e3cbccb09eb299d72ca418058209
records exact syscalls, full pidfd/cgroup closure and unchanged originals.
Opportunistic Python terminal-ioctl/cert-directory denials are irrelevant to the
required metadata reads and remain denied. The narrow source10 policy scope now
requires the two ACTUALLY observed process-getattr/link-read forms, preserving
all38neverallows, no file-body/ptrace/signal/ioctl/control/capability grant.
Final CIL, focused checks, protected module prequalification, full five-inert
positive component and strictgate11 remain pending. Existingd077/kernel5ec/
receipt6ba/index5d/policy443 allfalse and all canonical rolesOFF remain unchanged.

| Additional reproduced requirement | Smallest meaningful check | Gate and result |
| --- | --- | --- |
| Fixed authenticated broker process context and executable-link reads under helper_t | Actual22921/23093-23096 denials, exact two CIL forms only, unchanged38neverallows; one positive confined five-inert component after protected backup/original-EX module qualification | Candidate/focused/final positive pending; no metadata observation is job/retirement/writer acceptance |


Source10 final TWO-form CILa72eed2da6d81583efb434621d3923b5ed4a5304a9c8d1c5fad03481fca30686
adds only unconfined_dbusd_t process(getattr)/lnk_file(read); final policy tests
pass67/0.59s, peer74b unchanged. Copied strict comparison04586de48122791b1fb889cfb1d6392ce0da9d5daabb4bf94a6b143199b726c3
retains the same38 standing failures (NOT strict pass); AV-only comparison
a05610c3d890a9b6f2457df3dcfa60fee6b965c7c290d8964260701e4c9f06ee
preserves26 prior vectors at331 captured booleans and changes the complete helper/
observer effective allow expansion by only those two rights, no removals.
Public host continuityc7787b1edf772b98e5d21397217810de8d1b96612a02f0fcd5a76912e07c93b7
unchanged; copied binary never installed. Root-published candidate is38570B/
inode29938939/root0600, hash pinned before effects.

Reviewed owned policy qualification15810644 PASSES11.619s after fresh protected
policy/config tar+compare, original1706EX and full OFF proof. Old CILd077 inode
80332354 and receipt6ba inode61556809 retained WHOLE/RNR with exact attributes;
one priority400 module load produces actual kernel
c956f95839e837e65aec303c6381707a9f9fe1b9c033753af0f45b2d32395919,
new canonical CILa72 inode80406104 and version1 actual receipt
4c43d12234a3efdac1deee1b559b75eec12cf4e6f9a2e198f769b5a369f711e3
inode61565241/root0644/confSID. All other modules/booleans/fcontexts, canonical
code/unit/index/policy/current, stores/credentials/masks/locks and both NFS-ro
views remain exact; manual rollback prepared, no automatic rollback. Result
e7070e84e25f8d159eb07b7380df618d51a7f6689a7e9e280789b9f7655936a2
is explicitly candidate qualification against source9, not a clean source10
release. Index5dca/policy443a ALLFALSE/current128213298/peer e06 remain OFF and
stale until the final matching clean source10 genuine bootstrap; no role starts.

Actual full five-inert component2 PASSES4.852s under the new measured policy,
scriptbfe17fd3, receipt9b0f8a5f354bccddb007661b2de323fa77711d220194ef5464c0d1db0c9049cf.
Helper_t60053/start5632365, fresh UID/GID983/no groups/zero E/P/I/A/Bnd0xc0/
NNP1/Seccomp2+27filters; two real _engine_prepare/auxiliary snapshots identical.
All five identities manager21205, typedPAM21207, authenticatedkeeper21279(parent1),
broker-launch21288 and broker21289 pass twice; four protected image/kernel-inode
proofs remain, PAM retains no image-authentication claim.474 files/91146B charged.
No engine invocation/setns/API/RPC/retirement/job/archive effect; exact13 fixed
metadata/stores/cohort unchanged, full pidfd/cgroup closure. Earlier component1
failure and qualificationFALSE diagnostic remain preserved. Final technical
freeze and strictgate11 are next, then matching source10 build/install/recovery;
no installed retirement, writer/restart/rollback or production success inferred.


Source10 strictgate11 ACTUAL PASS: all9923backend/52deselected in1202.47s,
locked base/server/server+MCP wheel installs/import/help/version,179wire, required
functional metadata/no required skips, frontend unit/combined,16sandbox built
browser, actual200%zoom/320CSS controls and real API React read checks. Whole
gate1517.303s; private empty read-only NAS shadow/loginUID1000/nice10.
All1283 frozen source names/bytes unchanged. Rawlog205a4429913b5c3d3e1b8ebe119551725ab12b91a4d0adbfee1f2dccb605470f.
Task/current factual evidence only follows this gate; separately scoped docs11
checks precede clean source10 fixture cut/build. No installed retirement/writer/
production acceptance is inferred. Actual qualified a72/c956/4c43 pair remains;
all canonical roles OFF, stale source9 allfalse authority awaits new matching
source10 genuine proposal/bootstrap. Do not reload the unchanged module.


Source10 clean immutable owned-fixture assembly and guarded startup now PASS.
Detached source bab550088ed4a9010cd2555bcbc9b38759451b1d (main7894540 unchanged),
full snapshot65caf20d8a82628be22015b96fb4a385cce096b028b30cff704ef86dcf87d474,
bundle index29fc9ec30780ebc68710eaa97f2a4084faa8df7b306c8c65cba3b3c9986ec04a,
app image ad645eff3b1378f929e1a2e80aa456a002f7a8dc9e6fe5f31b4c00d8c1e4afb2
and UI523b0b6c81ac784c119c37116c29169d7f6276d0a0db55b5b11d1876a2ea53d9
are actually built, transferred and verified. All20 predecessor core CIDs/nine
images remain retained. Whole source9 prefix is preserved. Guarded/manual siblings
stage through the official installer with indices0136bb07/9665b14e and runtime
866943b9/13682492. One guarded selection yields current inode111251779.
First label wrapper refuses its stale policy assertion before effects; its full
failure remains, and the corrected exact-policy wrapper passes the same18 labels.

Fresh reviewed peer-only handoff retains old peer e06 whole, installs peer74b,
and does NOT reload unchanged qualified CILa72. Actual genuine source10 proposal/
bootstrap binds indexf09a9d33a0ba7794eda4474668c86e97a5f97be0414f15ec19a9b80607da03f8
inode61679678 and allfalse policy4779bf9653cc09e3d4072b9b34ff53e6231e13893ae759ea3e9b52fc309207a8
inode61679679. Previous index/policy original inodes are retained whole.
This resolves the intentionally stale source9 authority after the separately
recorded module prequalification; no prequalification is recast as release proof.

Ordered helper/worker/API/Caddy starts PASS once. Helper61884/start5917950;
worker62084/start5929137 CID97e246b2df199492efe918a0ddcb772ba94d8d7d138fdce6430317f86d7e3d46;
API62233/start5938951 CID3bab74cbfa9fa9a28623a20804fef7080c02d1cfac1980b91ed497ad085e4104;
Caddy62786/start5960823 CIDcdbcdadd9fb0a6a49f5f97e93d079465c6492854f3a5d392e80b6aa5a217ac56.
Actual receipt hashes worker566891fd0ba994bd47fa7c827c866844b529e67303e194355c4e834c4fc69ce5,
API049f36e8a3a06d813785264fd4e696b655ecdda859b026528f3ed7cb073b84ee,
Caddy865b0c0b4ac8f51244a28277d777f923b9c979cb40f930c38fd02218d3dd9d76.
Original locks/stores/credentials/SELinux Enforcing and confinement persist;
bridge/guard/targets/socket remain deliberately OFF, NFS aliases read-only.

Ten actual authenticated strict-TLS GETs PASS in9.657s: both root and management
bootstrap/version/readiness, exact installed UI shells and JS assets. Readiness
proves actual API-origin private worker PROBE, archive/hub/control/writable false.
Known owned-fixture donor is RAM/stdin-only verified through actual API Argon2;
no production credential source is used. Receipt6c3e3d82658becd8a883238c10492449453df16d32efea21da29fae7a8e37aa3.
No POST/job/permission/archive write occurred in these startup/read checks.
New public source10 browser driver ec3946ce is published without replacing the
source9 driver. Six-case installed browser followon1 is launched exactly once,
currently awaiting its original result; no success is inferred. Writer, lost-ack,
restart/rollback and production acceptance remain pending.


Source10 installed six-case recovery followon1 ACTUAL PASS240.303s: Chromium,
Firefox and WebKit at root and management prefixes. Preserved original failed
schema2/record85ccd/keyb5e/authority is restored verbatim for the first case;
five remaining contexts migrate schema1 normally. Each single explicit own-key
retirement returns200, presents historical outcome unknown/request retired,
retains original handles and reconciles on GET-only reload. Exactly6 retirement
POSTs, ZERO jobPOSTs/admissions/archive writes. Original9 fences and six historical
receipt/result pairs remain unchanged. Actual15-entry disposition SHA
c365cc815002195ff0392789d18875144097b6b3335e9877e224ef89326b4556;
report31ee95e02efd75e38076a5efc09f28d4b619f2b805ed7dc3ce222ec9d42e3caf;
root result8224628b5ce68267f1cdfd102e7d7856a563fbe7bd66048effd7a00f14bffabb.
Browser CID320f9e913f7738d6a89f85ef388575141d4ea7e59f82945708479de86a7684ff
closedPID0/exit0/empty cgroups; contexts and browsers closed. This is owned
installed proof, not recovery of the separate production key.

Prepared lostack driver review catches the known Firefox first-response-event
status ambiguity on its second reload BEFORE execution. New reviewed2 driver
92836c987489e18b21ce7015aecf82cda0b79312a76d54288f34b1456e2b60ff
retains original200/401 event separately and requires exact typed admitted body,
original operation/archive/route/principal and ordinary terminal UI; GET-only
reload/exact-single-POST assertions remain. Old draft84262 retained unchanged.
High review finds no remaining concrete driver/hook defect. After actual15-fence
success, reviewed Hub-only hook99f62e3f grants only Hub under original1706EX in
0.403s. Original allfalse policy inode61679679/4779 is retained WHOLE/RNR at
private root hook work; selected Hub-only inode11901892/d2eb9329. All original
stores/fences/roles/mounts/credentials unchanged. Archive/configuration/control/
schedule/observer remain false. Manual preserving restore prepared before effect.
No lostack Plan job has been submitted yet; launcher qualification remains pending.


Source10 installed Plan lostack ACTUAL PASS271.453s (reviewed launcher28d3b813,
driver92836c98): six real202 admissions, exactly ONE PlanPOST each, controlled
acknowledgement loss, GET-only original-operation/result recovery and reload.
All3engines/bothprefixes pass; actual installed API SDK validates all six new
receipt/result references, hashes and result Envelopes. Original15 fences and
six old terminal receipt/result pairs remain exact. New operation IDs:
5afd386b24de498e89836c187fe27ce7, a4ed4e6b6137ddfbfb4ba66df40d4613,
d24949432c49547c3fc6a1e4617e9a8f, e5a4146edad2030690a27d83c7e032c4,
3c58d8398163957765f69ea6f55be97c, 27b62e75a412b678caa017e8965bec05.
Result3e4c3e253a4c7e96da80a9f17cd745d0f91c09d2fe4c5f7bdb31b59639cc493f;
report5c356995e744d43aac96c380e6e2c9f2f1dda9d0c791bf2a585df1732ca693b3;
CID67465fe466f2a035300d63f4a08a4cd52e17fed66553caee670bc493fe724430
closed exit0/PID0/no live browser cgroups. No archive grant/write or retirement.

After known outcomes, reviewed manual original-EX Hub restoration PASS0.490s:
original allfalse61679679/4779 restored WHOLE, granted11901892/d2eb retained;
restore208fa74f389b753e37b5d6d266d229e8d030bb9e70d09c5f7b00266dfa6853e8.
Fresh protected critical backup2 (includes actual fstab/bridge/guard leaves and
absence of target mount units) PASSES1.483s, tar9041920B/inode95245929/root0600,
receipt957f2640251992d495abca9da86f37f86ade868c302bebf97ec915530045b134.
Actual graceful retention drain PASSES9.864s: Caddy, API while worker/helper remain,
worker then helper; each original live CID renamed and stopped without removal,
PIDFD/task/cgroup/libpod closure proved. All23 core CIDs now stopped, nine images/
tags and original five inert983 actors retained; all original store bytes compared
in RAM, marker15 unchanged. Receiptbecfcc8f04c71868390ff9cf70f3dcdd9860e89eabba4fded554ed8d916d55b1.
Postdrain local-state tar/compare PASSES0.942s, tar122880B/inode12034346/root0600,
receiptb6f9d2b0a897cecebefdbbef09c092f026193d6f45386bed7fc5fb38c9b3aaf1.
All original six locks/credentials/old flat socket nodes retained, selected listeners
absent through normal application cleanup. NFS aliases remain RO, Enforcing,
bridge/guard/calendars OFF and legacy masks exact. No writer selection/remount yet.
Current-boot-only writer next-action reviewab6e2fb2 keeps existing connection and
local policy byte-exact; no fixture persistent mount unit exists, no new boot
support is inferred. Official writer selection/matching bootstrap/remount/startup
and writer/restart/rollback acceptance are next; production remains unchanged.


Owned official manual-writer selection ACTUAL PASS2.616s, reviewed switchc4974e5b,
receipt1393402a86d88ff38103d2584b6643b05c5ea3d31ff7158f88e54bddf46abcee.
Current now inode111274684 -> releases/0.3.1-manual-writer; original guarded
selector111251779 retained WHOLE by same-FS RNR. Both siblings stay immutable;
all nine binding inodes/targets,23 stopped CIDs/nine images/stores/credentials/
locks/guarded authority remain exact. Caller EX guards released for official
installer sole original1706EX. All roles stay OFF and both NFS aliases stay RO.
Genuine source10 writer proposal PASS1.141s under renewed originalEX:
index1a557c77a617fa8ca080f31b62c14e3269edb36fe5ec3b70b1e0b35c8cbefdbb,
proposal445de78d81f52e3eb6dfb78107f0af2b5a0324445946fd8a3a80300229e16b61.
Matching reviewed bootstrap PASS1.301s:
5458ffaf1c45c5e59775a002d5f47ce7ee57939b65d5c6d6f12b4d290a1cdeb5.
Canonical writer index inode61681920/1a557, allfalse writer policy inode61750347/
ce856e2c2ad443d1bfc82717c1079a2e5b5316d66bd060810bdd480a7788ceda.
Guarded index61679678/f09 and policy61679679/4779 retained WHOLE/RNR before
publication; original lock/runtime/store/credential metadata and all state bytes
remain exact. CILa72/kernelc956/SELinuxreceipt4c43 unchanged, no module reload,
activation, startup or archive effect. Controlled local remount and ordered writer
startup are separate pending reviewed steps; no actual writer success inferred.


Reviewed existing-connection loopback remount ACTUAL PASS0.986s; receipt
139a79bbb7cee74469f4e87110dfec94c517093bd9774b996378a02d6e8dc546.
Both original mountIDs345/346,parent71,device0:48,shared274,source127.0.0.1:/,
protocol/security/transport/options remain exact except RO->RW at both VFS and
shared superblock. Original1706/2004/store EX held; full OFF/23 stopped CIDs/
nine images/five inert actors proved before effects. All original stores/locks/
credentials/fstab/bridge/guard/kernel unchanged. Manual exact RO reversal saved
BEFORE effects; no automatic fallback. No archive files read/written or writer
identity/capacity inferred by this mount-only proof. Production NFS unchanged.

Writer metadata prestartup PASS1.437s d34c86a7b35252b6a9633b898c24e0453974bfe75045394c05662aefd422263e:
all actual retained state/labels/bindings/engine prerequisites pass, only named
reload/READY/ordered-start blocker remains. Reviewed helper-only start PASS3.439s
f15889e12929ca89a3c802851086288ddb93045dd8920f5b020884299c9677bf:
helper72521/start6123853/helper_t/root0/c0 E/P/B, I/A0, NNP1/Groups983. Genuine
READY binding index1a557/policyce856; both manager reloads preserve stable packaged
hardening, manager/cohort/default environment. All application/bridge/guard/target/
socket/legacy roles remain OFF. Writer worker-only start683a2e7a is launched once,
awaiting original result; no worker/API/Caddy or job success inferred yet.


First actual writer-worker qualification FAILS4.406s after sole NotifyREADY start.
Worker72706/start6136749, controller72703/start6136748,
CIDac3164b0c4cfffecb3dd9aa87923569fb58be3bf9c35af167525a10f1b3ccc45
is writer_t/privateMCS401,483 with zero capabilities, NNP/seccomp, network-none,
secret-free masks and requested RW bind. Actual payload archive row578 is VFS RO
on device0:48 while shared superblock and both host aliases are RW. Raw original
bd8fbf1833fd70b0a492c6f893caf70f2bdb0f2b56caa18ac5dae85ac4c37cd7
and failed controller/first outcome remain preserved. No API/Caddy start, archive
permission or job occurred; worker READY is NOT counted as writer acceptance.

Actual bounded namespace inspection confirms keeper21279/start2712684
mnt4026532304/user4026532303 retains RO aliases540/541 (master274) with RW
superblock. Conmon72703 shares that namespace; host manager21205/PAM/brokers
remain in host RW view4026531841. New worker mount578 inherits RO. Installed
Podman is6.1.0-2.el10; pause.pid44:150 names21279, ns_handles/.lock absent.
All five original engine lock/SHM inodes/SIDs remain intact (metadata only).
A first read-only metadata collector fails its inherited cwd permission before
engine query; corrected collector chdirs to / and preserves both outcomes.
No namespace/migrate/nsenter/kill/unlink effect is attempted.

Protected fresh failed-worker backup0074 PASSES2.180s, receipt
b25f2518287d7e1b3f13dfb13722e163439104c84f6ce26337384a1130ba3623.
Reviewed single-worker/helper graceful drain7c954 PASSES6.722s, receipt
cb656e37b462d6a5cff18a21462cab338844c7099159d58ce9c622901666e862.
CIDac316 is retained as web033-source10-writer-ro-failed-worker, exit0/PID0,
original PIDFD/task/cgroup closure; helper72521 also closes gracefully. All24 core
CIDs/nine images, original five inert actors (including old keeper), original
six domain/runtime/store locks, credentials, all15 fences/12 terminal pairs and
writer allfalse authority remain exact. Host aliases remain RW; no archive job
or file write has occurred. Old23add drain code is retained; only three inaccurate
evidence prose strings change in final7c954, executable AST otherwise identical.

Contracts/invariant/ADR165 now explicitly require keeper AND payload VFS proof,
with a separately reviewed fully drained rootless namespace handoff for inherited
RO views. Preserve bridge dependencies when selecting individual manual roles;
no boot-policy change is inferred. Exact Podman6.1 primary source confirms its
supported no-option migrate retires a known inert pause and may migrate old
Conmon PID-file metadata. Root's conditional review permits only that named
metadata change after coherent protected engine DB/sidecar/old-config backup and
complete structural comparison; no runtime/DB/renumber/reset/prune flag, unknown
executor kill or security weakening. Supported turnover remains PENDING; no
success is inferred. Final actor/startup snapshots must supersede old keeper
pins explicitly; durable activation and completed format/browser drills must
not be replayed. Scoped docs12 checks run under private RO NAS shadow; result
pending at this entry. Production remains unchanged.


Scoped docs12 fails only the human-audience checker on an execution-package ID in
new ADR165 heading (68pass/1fail); raw failure/log remain. Remove that identifier
from the human heading, without weakening the checker. Scoped docs13 then PASS69
in8.165s under private empty RO NAS shadow/loginUID1000/nice10, shadowlog
acfe99d96ec5f41f966ef56e978b3276167d89dcd756c68522aefb928982f896.
This is documentation verification, not another technical gate or writer proof.

Fixed engine DB/owner metadata probe419c ACTUAL PASS0.380s, receipt
8c93ba12a3f8a534e0f5e994208085f81563312a515414dd332abb2e0ba76ce4.
Canonical graph db.sql inode94907898/983:9830644/643072B; all SQLite sidecars and
legacy DB paths absent. No FD/map owners or inspection errors. Old keeper21279
is the sole old-user/mount namespace owner and has zero children. No DB/sidecar/
engine-lock/SHM body is opened or mapped by this probe. A coherent private opaque
DB copy with queries exclusively on that copy is now being prepared for review;
no canonical SQLite query, migration, namespace retirement or replacement occurs.


Opaque before-DB copy29805 ACTUAL PASS0.583s, receipt
b58f999e3299a3443bab539d6e21d25e52b709604218c51e4d09bf4999dae3d5:
canonical643072B unchanged, private original-db.sql inode44936035/root0600,
copy integrity ok;24 stopped Config/State rows and possible Conmon path changes
identified through COPY-only SQLite. No canonical SQLite/library open or engine
call. Root review catches JSON storage as actual BLOB (private-copy typeof),
while first unexecuted0a02 verifier expected TEXT. Reviewed2 baa5c5a1 decodes
str/bytes and compares storage classes; original draft retained. Its exact
logical function passes against the actual private copy (12 tables/25 schema
objects/24 Config+State each); no effect in that decoder check.

Reviewed2 official namespace turnover executes ONCE. Actual no-option Podman
command exit0/stdout0/stderr0. Known inert pause21279 closes, old namespace has
zero owners, four original manager/PAM/broker actors remain byte-exact in their
recorded metadata. Original pause inode44:150 retained through explained same-
tmpfs root0700 evidence hardlink; canonical pause is now absent. No fresh engine
namespace or application role is created. The controller then FAILS1.334s at its
postcondition requiring all planned Conmon updates. Preserve the first code,
command/closure/copy observations and failure; DO NOT rerun migrate.

COPY-only diagnosis shows ZERO Config JSON differences, unchanged schema and
all other tables; both643072B retained before/after DB copies are BYTE-IDENTICAL.
Zero change satisfies the allowed-delta scope more strongly than the optional
Conmon migration; the first verifier incorrectly required those changes. A
separate read-only original-effect qualifier is being prepared for remaining
state/lock/kernel/image-identity checks, not a new migration. Exact pre-migrate
raw images.json bytes/meta were only in the exited controller's RAM, so equality
of that raw file cannot be claimed retroactively. Use recorded nine content-
addressed image IDs/tags/digests, unchanged Config image references and immutable
artifact proofs; do not invent missing raw evidence or widen image revalidation.
Appstore exact bytes/meta remain recoverable from protected b25 backup/tar.
All permissions remain false and roles OFF; no job/archive write, fresh keeper,
manual kill/unlink/nsenter, fallback, activation, module reload or production
effect occurs. Preservation qualification and corrected writer startup remain
pending. Contract amendments preceded this sole supported turnover effect.


Read-only qualification of ORIGINAL sole turnover d47d PASSES1.319s:
bc5d6a79299d71425da4d17b7dadcda421e3cd89e2f583a07cd3b5ee02e1a27d.
Original controller remains failed and preserved; official tool is never rerun.
Before/after DB copies are byte-identical; all schema/JSON/storage classes and
all24 Config/State rows unchanged, actual Conmon changesZERO. Full selected
immutable prefix, config, API/worker/activation stores and secrets match protected
b25 tar in both bytes and metadata. Original six guards, PHC/HMAC/permissions,
kernel/CIL, masks and RW host mounts retained; five engine inodes/SIDs/size/owner/
mode/nlink exact except explained coordination timestamps. Nine image IDs/tags/
recorded digests and Config references retained, with raw pre-image-byte baseline
limitation explicitly recorded rather than invented. Original pause44:150 is
retained privately/nlink1; canonical pause absent, old NS has no owners, four
original inert actors remain. No new namespace/keeper/role is created by this
qualifier. A separately reviewed single normal engine metadata startup will
create/authenticate a new RW namespace and a superseding actor snapshot before
corrected writer startup; that effect remains pending.


2026-11-05 continuation: single normal cleanenv engine metadata startup creates
authenticated fresh keeper74076/start6466399; actual keeper VFS and superblock
RW. Receipt0e425e3ad224a1621af8b06d4505277f3b01284820e03bf46647403645f556d0
PASS1.706s; superseding cohortb6a9c0c16b02680aea00eaa270d9f512e7c65f3baf8f3962996ee0cea364ad78.
User/mount namespace NUMBERS recycle; new PID/birth/pause inode44:2478 and old
namespace lifetime closure, not numeric inequality, prove fresh namespace. Four
original manager/PAM/broker actors,24 stopped CIDs/nine images, DB bytes, original
locks/credentials/stores and allfalse policy remain. No migration replay.

Writer startup2 binds the fresh receipt/cohort, not stale original startup pins.
Preflight26bfe1ee55589d98e169dec51d7d59ae59a8dc0525aad94398f0cec4f97cb6f1
PASS1.444s; helper2e3cd107f1a52f61a994d3a39d8673e996709d5832843602fb71e1d30e1fc9e9
PASS2.942s, PID74379/start6496632. Workerbe6f1af748e954e40081777e8377f501137560fa02f44461d7f0733585e985a7
PASS4.777s, PID74569/start6509103/CID0ac0ae3c, writer_t/MCS120,987 and ACTUAL
payload VFS+superblock RW, caps0/NNP1/seccomp2/networknone/secretsnone/original
instance lock18402599. API30e7fc0f6afea7703995e3673446ef5f7ec5507d6684826263c28cead512a1fa
PASS9.442s, PID74744/start6521558/CID845a56fe, writer_t/MCS723,1019 actualRW,
exact secret identities and FD-anchored original socket. Reviewed Caddy2 script
18418c58 starts once, PASS1.910s, PID75468/CIDcac04f00; container_t/no archive,
exact original TLS secret IDs and hardened listener8443. All6permissions remain
FALSE, bridge/guard/targets OFF, all schedules disabled/legacy writers masked.
No Sync/Verify/refresh/archive write or production effect. Ten strict TLS/UI/API
reads are in progress; subsequent writer positive/negative/restart/rollback
acceptance remains pending. Original failed worker and all predecessors retained.


Installed writer TLS/read1 c38795fe fails first GET /ui/bootstrap.json with
HTTP502/emptybody after strict TLS and actual API Argon verification. Original
failed-read-observations preserved; zero POSTs and no automatic retry. Caddy
logging is configured discard; bounded structured journal and socket diagnosis
find original API inode10038/listener FD6 (observed, not hardcoded authority),
correct shared parent1330/9830700 and socket9830600/container_file_t. Original
Caddy remains container_t/MCS169,1010 while API is writer_t/MCS723,1019.
COPY policy query lacks container_t->writer_t unix_stream_socket allow. Actual
kernel libselinux AV3 confirms connectto/read/write/getattr/getopt/shutdown
allowed0/sequence8; standing domain-domain dontaudit suppresses read/write.
First AV binding diagnostics1/2 TypeErrors are retained; third succeeds, no
policy or request effect. Exact minimum IPC repair under high review is one
directed connectto permission; ordinary I/O uses each caller's OWN socket SID.
No cross-peer I/O/process/file/archive grant or MCS exception proposed. Actual
installed frontend remains FAILED until a new qualified selected source proves
it; startup PASS alone is insufficient. All permissions remain false.

Independent actual writer API SDK read-only storage qualification2 PASSES3.162s:
original expected sentinel, actual NFS mount RW/staging same filesystem, capacity
11.1GiB free/39.7GiB total/4.0GiB reserve, mapped981 and measured installed Sync
lock budget3600s. All four write probes SKIPPED, original config/guards/stores
bytes/metadata unchanged. Controller1 fails before any SDK invocation because
fixed metadata helper lacked fields; retained and corrected controller2
1b3270617bfd90742c715910cacfafba2d8d7fdc199a6d5794f9d26449bb3c61.
This is storage-boundary evidence, not admission or persistence proof. No
Sync/Verify/refresh/archive write or production effect.


Directed writer IPC repair freezes one CIL form1fb78db7237424904633ccc4681ff40b037fc7ff3a65068464225d2c7c543997.
Focused red demonstrates missing connection; final73 policy tests pass after
closed allowlist adds exactly the same directed connectto pair. All38neverallow
forms remain byte-identical. Copied strict comparison9e874e6d retains SAME38
standing failures, explicitly NOT strict pass. Copied AV comparisonf2ce072d
compares full effective vectors: container_t gains only writer_t Unix connectto;
writer/helper/observer vectors, constraints and MCS membership remain exact.
No peer I/O/reverse/archive/file/process/capability or category exception.

Fresh actual backup326c2a1a5295ec4526e68e823430da40e94c385a5f817e603acb03d7d9e5f2ff
PASSES2.995s, tar10045440B/inode36600894. Full actual drain1509a6eff21d0933a4ecf2e97c1fc8a262e831dbb85cab6b4a4dfd4c3a125299
PASSES13.025s: Caddy/API/worker/helper graceful closure by original PIDFD/task/
cgroup, all27 retained CIDs stopped/nine images unchanged, fresh five-inert b6a9
cohort remains. Original12 terminal API pairs/15 fences, six domain/runtime/store
guards and PHC/HMAC/secrets preserved. Source10 three exact CIDs retained as
web033-source10-writer-before-source11-{caddy,api,worker}, no predecessor deletion.

Reviewed2 policy qualification9f68 PASSES15.102s, receipt
1bf9058eba272257fe6b65346f8f1fb8b2d4c7501c27e2dd568795c54cccf3bc.
One priority400 CIL load follows protected policy/config backup/compare, exact
state-byte/selector revalidation under original1706EX and manual rollback prep.
Original a72 CIL inode80406104 and4c43 receipt61565241 retained whole under
/root/web033-source11-writer-ipc-policy-qualification/source10-{canonical.cil,selinux-receipt.json}.
New CIL1fb inode80475246/kernelab7b3d08aeabac4f6161c8cd959ba850cbbf907d692e1e9591ab7f92a22bc363,
receiptf0bf0ccb4ed089d87145fb3147b5073b9d67e004260df75b88423bbf05ab5261
inode61666176. All booleans/fcontexts/unrelated modules/code/units/stores/locks/
credentials/masks and Enforcing unchanged. This is policy prequalification only;
source10 index1a557/policyce856 ALLFALSE intentionally stale, all roles OFF until
matching clean source11 genuine proposal/bootstrap. No repeated metadata/PAM/
recovery/lostack/native/format/component workflow is required by this one edge.

Actual protected RO installation-window remount2395a9d88a51b353e0adb8810bfb750343621808d4f3ae005bf7556216ef4b6c
PASSES1.540s under original EX and fresh full drain. Both original host aliases
345/346 and superblock RO, dev0:48/source127.0.0.1:/ and all other fields exact.
Fresh keeper74076 remains inert; no second namespace turnover. fstab/bridge/guard/
locks/state unchanged, no archive-file probe, job or production effect.

Strict gate12 completes GREEN:9929 backend/52deselected in1229.22s, documentation
alignment216 human documents/29helpers, wheel build and all3 locked profiles,
179wire plus required strict web/unit/browser/200percentzoom/320CSS/realAPIReact
read stages pass. Full1544s; source1283 names/hashes unchanged and no source edits
during gate. Actual gate result/log retained under /var/tmp/web033-validation.
Only current/task factual evidence is updated after the frozen gate before the
clean source11 cut. Source11 build/installed writer TLS/PROBE, two positive jobs,
finite storage negatives, restart/missing-companion and compatible guarded
rollback remain pending. Source/unit success is not installed acceptance.


Clean matching source11 cut3c8eaa6e/treec49b31b5, source snapshotfb3430cb,
builds reproducibly; app ee702de2/UI4ed3c421, wheel f6ae6572 and main JS2409dca5
are byte-identical to source10, retaining unchanged recovery/lostack evidence.
Official sibling staging6427faa8, public labels e2d446de and writer selection
5c8cba6c PASS; current inode103674864. All27 prior CIDs/10 images and source10
prefix retained whole. Genuine helper proposal1b3e43b8 and bootstrap58a9292b
PASS with candidate cb985fdf/policy85572b06, inodes61675462/61675463, all six
permissions false. Old index61681920/policy61750347 retained whole by RNR.
Unexecuted bootstrap draft CHECKS and reviewed2 bytes/parser-call defects caught
before effects; reviewed3 uses actual closed deployment parser on candidate bytes.
Reviewed remount4c6c37c6 PASS0.948s under original guards and actual full drain;
both original host aliases and fresh keeper VFS/super RW, other options exact.
No archive file probe/job or production effect. All roles remain OFF pending
separate read-only prestartup and ordered actual helper/worker/API/Caddy startup.
No harness expansion or repeated green gate; next evidence is direct installed
product behavior, one Sync and one fullVerify by original handles, followed by
finite negatives/restart/guarded rollback. Production remains unchanged.


Source11 actual prestartup608aa715, both-manager reload/helper810f86ec,
worker883a8550, API81b8e2c0 and Caddye6ed852a PASS. Actual payloads worker79837/
API80046 use writer_t/private MCS and RW NFS; Caddy80460 retains container_t,
helper79576 confined, hardening/credential isolation/original guards preserved.
Strict TLS/UI reads3e91da8e PASS9.451s: ten actual authenticated GETs across
root/management return200, exact source3c8e/UI4ed/JS2409, writable storage and
API-origin private worker PROBE. Actual SDK storageb5d59cf7 PASS2.986s: correct
sentinel/mount/staging/capacity and installed3600s Sync lock budget; write probes
skipped. This closes source10 frontend502 after the one directed policy edge.

Minimal archive+Hub grant d93bcf1a preserves original six-false policy61675463
whole. Positive3 sends exactly ONE Sync POST, admits original operation
75b07d65288dbce3419bb72e268d6b79/domain853a3cee29ee444b93ce7b87a4292916, then
failsHFARG002 before archive-lock acquisition because fixture config disables
tokens while installed server explicitly supplies a token file. This is the
documented contradiction in configuration section7.2, not evidence to weaken
credential handling. Original failed receipt/result5144a302 retained; no
verification POST. Artificial holder81737 holds original27:1706EX, observes the
original GET200 but cannot prove waiting_lock because original is already failed;
failed receipt1754dc01 truthfully records this and cooperative release. Browser
closurebb108bf5 independently proves all contexts/browser/CID24bbb tasks closed,
sole Sync POST and zero verification POSTs. No automatic replay or retry.
Original policy61675463 restored whole/all six permissions false. Fresh critical
backup and full executor drain precede a separately reviewed fixture-only token
configuration correction; original configuration will be retained whole. Any
subsequent positive intent is new after that relevant prerequisite change, with
all13 historical pairs preserved. Production unchanged; no new source defect or
reason to repeat green gate12, native/recovery/lostack/format checks or harness.


Fixture correction prerequisite: fresh backup777dd149 PASS2.692s/tar10209280B
includes all13 terminal pairs, full drain edbb98ee PASS11.528s retains all30 CIDs
and ten images, exact PIDFD/cgroup closure/fresh five-inert cohort and original
guards. Reviewed token-mode correction5b4a137e PASS1.047s under all six original
guards: only disabled->optional enum changes, empty repository selection and
other parsed fields exact. Original config inode61323382/raw8838be36 retained
whole as /root/web033-rootless11-fixture-token-mode-positive4/original-disabled-config.toml;
new inode12098345/rawa8547b57 preserves0:983/0640/application_conf_t. No token
value read or production configuration change. Both aliases remain RW, roles OFF
and all six helper permissions false. Separate prestartup2 d707d7cf PASSES
against all30 retained CIDs/13 terminal pairs, actual restored policy metadata
and selected corrected configuration. Retain original successful daemon-reload
evidence810f86ec; no repeat reload is needed for this configuration-only change.
Ordered helper/worker/API/Caddy startup2 is next, followed by fresh config-aware
storage/readiness and separately scoped positive4, preserving failed positive3.


Source11 corrected-configuration startup2 PASSES: helperd7ba0fb3/PID83822,
worker3baff788/PID84007, APIf728d7cc/PID84185, Caddy33832951/PID84606. No manager
reload repeated; retained exact source11 initial reload proof810f86ec. Ten actual
strictTLS/UI/PROBE GETs0372bf48 PASS9.905s against corrected config. Installed
SDK94865f5c PASS3.002s: token resolution succeeds through ResolvedToken.has_token
without secret output/Hub call; correct sentinel/mount/staging/reserve, four
write probes skipped. Identity mismatch HFMNT007 and actual-total-exceeding RAM
reserve HFMNT011 refuse at named storage boundary, not HTTP admission. Earlier
SDK diagnostic failures retain wrong return-type assertion and Python-mode
model_dump Path rejected by strict StorageConfig; final uses documented JSON-mode
round-trip. Neither failure submits a job or changes application source.

Positive4 stops before POST because artificial helper preacquire30s expires
during browser opening. Closure7ff20b7f proves zero job POSTs, all browser tasks
closed, original EX never acquired and14th history pair not created. No repeated
gate/startup/storage or policy grant. Positive5 uses the same qualified state
and starts holder only after browser ready, with tool calls coordinated together
to avoid chat latency. Independent holderde01c911 PASSES original1706EX/waiting
original-ID GET/release for admitted original1d37100ce25a915d25071954c47a66e1.
Original Sync SUCCEEDS exit0/run578695dede40499faa38ebc272b6dfd2; terminal UI is
observed. Driver then stops because unscoped completion-text locator matches
both Jobs region and recovery article. No Verify POST and NO Sync replay.
Closure d59ec2fa proves browserac5b8978 tasks/cgroups closed, exact original POST
count1. Actual installed SDK proof1cc419d6 reads that same original resultb7c1424e,
run report895ccd91, committed transaction373f10171a7746bf9c20dba1ba082f2c and
catalogdaba52d1, with required completed checkpoints. Thus actual writer Sync
persistence and original lock interlock pass despite driver NOT passing.
First proof launcher quoting fails before guest execution; retained; second
readonly invocation passes, no repeated job.

Finite followon6 is running: restore the byte-pinned ORIGINAL pretransmission
Sync record for GET-only original recovery/reload using scoped Jobs-region
completion locator, then submit full Verify ONCE. Existing successful Sync is
never repeated; prior14 API pairs/15 fences and all stores/credentials preserved.
No new aggregate harness, optional matrix or repeated green gate. This leaves
actual full Verify, missing-companion/drained restart/guarded rollback, WEB033
commit and REL018/OPS028/OPS029; production remains unchanged.


Followon6 sends zero POSTs, recovers original intent/operation/result correctly,
but Jobs-region status locator times out because a restored session has no
latest-admission panel. Actual component source shows terminal status belongs
to article aria-label="Recovery record <recordId>". Closure8646e84f proves all
contexts/browser/CID tasks closed and zero jobs submitted. The narrowed original
record article locator is then used; no Sync or earlier workflow is replayed.

Followon7 ACTUAL BROWSER PASSES both cases: exact original Sync recovered/reloaded
using GETs only, then ONE full Verify202/originalcd43c3364065c2f1fdcb6beed7549594.
Verify SUCCEEDS exit0/run079bfd122fa247b3bff7e732098716c1; exact API and private
worker result3b9d7746 match. Browser report e932f2b2 passed/closed, with zero Sync
POSTs and exactly one Verify POST. Original launcher exits1 AFTER successful
browser because it overstrictly expects original global-lock timestamps unchanged.
Full comparison finds ONLY global1706 mtime/ctime changed by the legitimate
locking._write_holder write/clear; inode, uid/gid, mode, nlink, size0, xattrs and
EVERY other fixed/store/credential byte/metadata exact. Original failed assertion
is retained, not labelled launcher PASS.

Separate READ-ONLY postqualification7263bbf682dfdb9145ebdcc4538170be9fc6f310f739640ed1f7fc966f63a7c3
PASSES5.912s without any job/browser rerun. It explicitly qualifies only those
two mutable diagnostic timestamps, then runs remaining original SDK/report/
catalog/private-worker-result/role/cohort/mount/browser-cgroup checks. All15
API receipt/result pairs, one new worker pair, original15fences/c365, PHC/HMAC
and authority identities preserved. CIDa1d555e0 is retained stopped0/alltasks
closed; immutable old histories remain exact. Both successful originals and
actual installed application persistence are now proven. No further positive
Sync/Verify is required for this fixture.

Reviewed policy restoration87ce0c0e PASSES0.462s after terminal originals and
closed browser qualification: original allfalse policy inode61675463 restored
whole, granted23732182 leaf retained. All six permissions false; helper/worker/
API/Caddy still active in qualified source11 writer mode, host aliases RW.
Next: fresh critical backup/full actual drain, original2004 missing-companion
startup refusal/restoration, drained writer restart and compatible guarded RO
rollback. Reuse green gate12/unchanged recovery/lostack/native/format evidence.
WEB033 is not complete, and production deployment/pilots/backfill remain pending.


Fresh pre-runtime-boundaries backup1be1d6279d655f5198d7ed89e6beb8dfd2049f45a282cd0047b70a0516814bac
PASSES2.554s/tar10485760B. Full actual drain98c0e645801e001526572a78d744f6dbbd4241082dc127f9045a3d3e24c26abb
PASSES12.677s with all33 CIDs/ten images retained,15terminal API pairs/one worker
pair/15 fences exact, six original guards and fresh five-inert cohort preserved.
All application roles/helper OFF; mounts remain qualified RW, permissions false.
The metadata-only missing-companion baseline as UID983 refuses BEFORE any
canonical change because genuine helper binding.json is absent after helper
drain. This is expected required helper-READY authority, NOT a companion refusal.
Original companion2004 has not moved or changed. Prepare prestartup3/helper-only
READY, retaining actual reload proof; all writer roles stay drained. Only after
that valid launcher baseline may the finite original-companion unavailable
negative be attributed to missing2004. No fake binding, alternate lock, source
change or repeated positive job is introduced.


Prestartup3 989386c9 and genuine helper-only READY0f67bef3/PID92407 PASS;
valid actual launcher baseline17ed09a1 passes as hostUID983 with all writers
drained. Missing-companion actual installed boundary19e91f59 PASSES2.463s:
under six ORIGINAL EX guards,27:2004 retained by same-FS RENAME_NOREPLACE into
root0700 /run private directory; sole actual installed worker launcher exits20
with closed PIDFD and expected boundary refusal BEFORE Podman start. All33 CIDs
and state remain exact. Original2004 is restored whole by RNR, only renamectime
changes; valid launcher metadata baseline passes again. No alternate lock, fake
binding, body read/hash, job or archive-file access. All permissions remain false.

Drained writer restart3 PASSES: worker0a4ad27f/PID92756, API239c055c/PID92930,
Caddy0775b97f/PID93342, confined helper92407. Post-restart strictTLS bb6aa118
PASSES10.706s/fourteen GETs: exact source/UI/two prefixes, real API-worker PROBE
and four ORIGINAL successful Sync/Verify receipt/result reads with exact stored
result bodies/run IDs. All15 API pairs/workerpair/15fences/credentials preserved.
No new positive job or repeat browser workflow. Only compatible guarded RO
rollback remains for installed WEB033 behavior before documentation closeout/commit.

Pre-rollback backup creates retained tar10567680B. First --compare returns2
because four role-evidence paths were supplied twice, not because captured
state changed. Original failure/full tar/logs retained. Separate completion
c8274c06 uses the SAME tar and all original unique roots, proves exact original
metadata/guard/engine/mount snapshot, compares successfully without recopy.
Qualified backup45f56310cb6e20b0d912a39f43b2afa7fde8ba9e8f885123194f27718d64b0a9
PASSES2.273s with original controller exit1/compare2 explicit. Full36-CID actual
drain for guarded rollback is now running; no selector/mount/policy effect yet.


Guarded rollback full36-CID drain92ea5f2cc350d9fc1f0707a76028894cad12b5f1906759517936b06f2824eb80
PASSES12.462s; all writers/helper OFF and unchanged state. RO remount1c62055f
PASSES1.024s under all six original guards: original aliases345/346 and superblock
RO, source127.0.0.1:/, dev0:48, shared274 and other flags exact. No module,
namespace, archive-file or boot-policy changes. Official guarded selection
56728e3e PASSES1.774s. Original writer selector103674864 retained whole at
/root/web033-rootless11-guarded-rollback-switch/original-manual-current-link;
writer release and every predecessor remain. New current103739019 selects
0.3.1-guarded-readonly, source3c8eaa6e, artifactfe598f74/runtimeb1cbf7fd.

Genuine guarded helper proposal6853962e PASSES1.210s; typed candidate1ea070a5
selects guarded-readonly and matching stage/image/runtime/CIL/receipt. Guarded
bootstrap380a43ba PASSES1.196s under original EX, publishes candidate1ea070a5/
allfalse policy1e38afd0 at inodes61794152/61794153. Original MANUAL source11
index61675462/policy61675463 retained whole in bootstrap/original-*; credentials,
HMAC, operation stores/15fences, guards, loaded policy and all bindings exact.
Some executed preparation scope prose retains "writer" from its origin; actual
closed candidate/profile/selector assertions above prove guarded selection, not
a new writer activation. No jobs or schema/activation replay.

Guarded prestartup87488cc6 PASSES against36 stopped CIDs/ten images and all new
state. Original keeper74076 remains inert with RO superblock; no namespace
turnover. Required next steps are actual both-manager reload/new helper binding,
ordered guarded worker/API/Caddy, strictTLS read-only readiness/original results
and actual SDK original report/catalog preservation. These are the final scoped
installed rollback checks; no new positive job or old browser/format matrix.


## Final installed closeout — 2026-11-05

Guarded rollback completes without another job or browser matrix. Both manager
reloads and helper READY pass (`1a309247`, helper96239), followed by actual
confined worker96430 (`b28891de`), API96649 (`12e6e59d`) and Caddy97069
(`387a4c1c`). Fourteen verified-TLS UI/API GETs pass in10.585s, receipt
`2f580545d16bbf64dc5bf5e3266a93b47652ad8d31b2766e24b8edfd7f0127f6`:
both prefixes and exact selected assets, genuine API-origin worker PROBE,
guarded permissions and original successful Sync/Verify receipt/result bodies.

Read-only installed SDK preservation passes in4.753s, receipt
`0d8aa032d851d83e214f9e66fb1fe49bba05200c68e48c08ce84b7c5a26eabec`
at `/root/web033-rootless11-guarded-rollback-sdk-preservation1/result.json`.
Original Sync `1d37100ce25a915d25071954c47a66e1` retains its committed
transaction373f1017, report895ccd91 and catalogdaba52d1; original Verify
`cd43c3364065c2f1fdcb6beed7549594` retains report666a045e,
catalog67a5abd2 and exact API/worker result3b9d7746. Sentinel UUID remains
fc118f3e-2b23-43e9-bc7c-24795b155031. Both NFS aliases and superblock are RO;
all15 original API pairs, worker pair,15 fences, six original guards, secret
identities and predecessor artifacts remain preserved. Current103739019 selects
guarded0.3.1; all job permissions false, schedules disabled, legacy writers
masked, SELinux Enforcing and hardening intact. This fixture is not production.

Evidence reuse is explicit: source5/source11 manifest source_files contain the
same operations.py SHA256b11e7348033750d12b1179c6be8d1b507bbad849ce3dc12801bb4d99b8554c79,
operation-registry.ts abf10d8624c63b9dee0f0c16e59b379d20b92b061cb416574b3da73013f8da3f
and session-controller.ts7922abb2e1a305d3c0f8f1e1adc16e570a10188766da2cf844fd59291ba0a765.
Exact predecessor durable/browser reader proof remains its original native/library
scope; rootless activation, migration, live authority and original reads have
separate actual installed evidence. Source11 wheel and main JavaScript are
byte-identical to source10. No format/recovery/lost-ack/job replay is needed.

Final technical inputs pass strict gate12 (`scripts/check.sh --require-web`):
9929 backend tests/52 deselected,216 human-document and29 helper checks,
package build/three locked profiles,179 wire checks, strict web/unit/combined,
16 built-browser checks, actual200% zoom/320CSS and real API React reads.
Elapsed1544.324s; all1283 frozen source names/hashes unchanged. Raw log SHA256
813fc970ea99713ed04dcaa91f149e2e8cbef82e57a7e6fda8234bbf162f7952.
Subsequent edits only reconcile factual evidence and task/plan/current/progress;
focused documentation checks cover those edits without repeating the strict gate.
All failed controllers and original reports remain retained with their actual
scope; supplemental read-only qualifications never rewrite a failed result.

WEB-033 acceptance is complete. REL-018 next owns release version/artifacts and
its required strict build gate. OPS-028/029 still own actual production selection,
genuine administrator recovery of the historical unknown key, controlled writer
transition, selected Sync/metadata-refresh pilots and bounded metadata backfill.
No production success is claimed and the parent plan remains active.

Final factual closeout passes focused documentation checks in9.217s, shadow
log47f7b9629fd6781a6992b2574e3eb495ba141bb9952d9b2cebb91f935584f2a7
(`web033-postgate-docs14-shadow-result.json`). Direct frozen-input comparison
confirms only the four task/plan/current/progress records changed after gate12.
