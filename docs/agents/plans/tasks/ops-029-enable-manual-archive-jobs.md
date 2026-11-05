# OPS-029: Controlled writer transition, selected real metadata/Sync pilots, one bounded backfill of existing current publications and final operational handoff

| Field | Value |
| --- | --- |
| Status | completed |
| Plan | [Job recovery and archive writes](../2026-11-03-plan-job-recovery-and-archive-writes.md) |
| Depends on | OPS-028, REL-020 and recorded production-write/pilot authority |
| Execution | `gpt-6.1-sol` / `high`; explicit task-agent setting required |

## Scope and acceptance

Controlled writer transition, selected real metadata/Sync pilots, one bounded backfill of existing current publications and final operational handoff.

The parent plan's applicable scope, acceptance criteria and safety prerequisites
are binding. No remote pushes, image publication, release tags, automatic
schedules, unrelated permissions, archive initialization, manual archive writes,
reboots, NFS disconnection or other-host effects are authorized.

## Contracts, invariants, and ADRs

Review the parent plan's affected contract and decision list progressively.
Record exact reviewed IDs, amendments and any new decision before completion.

## Validation

| Requirement | Smallest meaningful check | Required gate/evidence | Current result |
| --- | --- | --- | --- |
| Writer transition prerequisites | Completed genuine OPS028 recovery; fresh original configuration/store/disposition/credential/artifact backup and complete actual executor/helper drain; same original flock handoff | `scripts/check.sh` plus actual protected receipts | PASS: original transition705edb6a/35d55b87; fresh0.3.4 backupc35fcc9e/drain eb1ba640, actual pidfd/cgroup/UID closure and original27:3904 handoffs |
| Guarded-to-writer selection | Select already qualified writer sibling while NFSRO; exact index/runtime/source/image and matching helper authority/grants | Same gate plus official switch/retained originals | PASS: both official0.3.4 stages7fcccee7, writer selection/binding402f117f; original selector/index/policy whole inodes retained |
| Local mount and namespace transition | Reviewed persistent local mount override/remount without disconnect; proc1 and retained rootless namespace identity/rights; fully drained normal namespace handoff if stale | Actual current-boot mount/namespace receipts; original locks/guard preserved | PASS: initial reviewed installed6.0.2 turnover/newkeeper434678;0.3.4 temporary same-connectionRO window thenRWf885aeb2, persistent override and existing namespace unchanged |
| Actual writer preflight | Application sentinel UUID, exact writer host/export, mapped ownership, reserve/capacity, Enforcing role rights, helper READY before ordered roles | Installed application read-only preflight and fixed role/confinement checks | PASS: actual installed both-role SDK014ae06c, API-origin worker PROBE23a42f9b, worker IP denialb27cdf5a; ordered startup1fcca26d and finalhost6c739daa |
| Selected genuine UI/API pilots | Review one repository/upstream target/size/retention effects, then one distinct new Sync and one technical-refresh request; retain exact original operations/results/run/publication evidence | Actual administrator browser workflow and API original results | PASS: genuine installed UI selected Sync817691c1 and technical refresh807f0c5e, original results/screenshots root-protected7ac0214c; refresh response-body loss recovered by exact-key GET, zero replay |
| One bounded metadata backfill | Enumerate current publications; finite batches within256-repository/512-publication/shared extraction budgets; every eligible publication bound or explicit actionable failure | One authorized execution with retained inventory/operations/results/coverage evidence | PASS: one pilot plus five distinct UI batches32/32/32/32/27;156 bound observations, zero write failures; installed coverage/preservatione6a0ca95 and149 incomplete diagnostic actions0e257d50 |
| NFS scope and final handoff | Only required opted-in application NFS checks within approved scope; actual writer state/rollback and remaining independent holds documented | Scoped NFS result, repository gate, factual docs checks, WP commit | PASS: six scoped read-only actual NFS checks2.20s; default gate12d17fdf and strict gate79c38bf1 cover final technical inputs; final factual docs checks recorded below; no disconnect/NAS change |

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

Completed 2026-11-05. All original eight-package observable acceptance criteria
are met through the recorded source, owned installed and actual production
evidence. This is current-boot manual operation, not unattended boot acceptance.

Production selected `0.3.4-manual-writer`, source
`9756c70f939f0a94aae28eb6c1a2d776c886b0e9`, app
`418edbe7e0f0e08c75a4d95ff75c5070d68c1a00f50afb7b912cee347ed1dc18`, UI
`40c4324a1cee1eb89f179b1902440da2c6905af12a3d1d7554443034d0bdb329`,
writer47-file index `bea2840db9d3efdfead64ccd57c03cc066c50f98c9c157f05cc24433f95298a0`.
Helper index `91d8e4ede6f09198db84ecb9ba33ec3ac1073f9a4fb7a67d28ee5bf9bc739020`,
policy `343378f26468786461d4991206fc017aaf02dbe698f5a68f4a22de051b7fcc05`.
Original grants archive/configuration/Hub true; control/observer/schedule false.

Fresh0.3.4 backup/drain/rollback preparation precedes all protected effects.
The complete API-first actual executor drain, noncreating original-lock handoffs,
temporary connected NFSRO stages/selection, exact18 leaf labels and measured
matching helper binding pass. Existing persistent RW override, authenticated
keeper434678/user4026532694/mnt4026532695, engine locks and kernel policy are
unchanged. Same-connection RW restoration passes; no repeated namespace migration,
module install or first intent activation. Helper READY precedes worker/API/Caddy.
Both fixed writer roles prove actual RW export/dev0:70/writer_t/separate MCS,
zero capabilities/NNP/seccomp; worker networknone/IP socket denied ENOSYS38 and
secret isolation retained. Caddy has no archive. Original config, candidates,
credentials and unrelated grants retain original bytes/inodes.

The selected0.3.4 sizing precedes reviewed Sync
`817691c13ea8fcc5845bd6f9239c48e8`/run `3b4b3ba0af1842538829386bcb6a1f07`:
upstream1886570b/current, eight files1030096B, estimated new bytes0 and max3/one
retained. Genuine installed UI and original API result succeed/up-to-date;
download/prune0, publicationb4d95efd/gen1 preserved. HFWRN011 stays visible.
Technical refresh `807f0c5e5494d00cabcc6f0196eeec64`/run
`304b118f7bea428aac0f6b0085c6717f` writes the exact Morino GGUF observation,
partial/exit0. The observer lost the HTTP202 body; preserved Basic key
725c0738-d9f0-483c-be50-06aeaae4beaa recovered that exact admission/result via
GET, then supported operation-ID import shows installed UI completion. One POST
only; both observer failures are retained, no replay or product-source change.
Earlier original failed4050dbaa and retired_unknown historical request remain.

One finite backfill reuses that exact pilot and covers155 remaining current
publications through five distinct explicit installed UI submissions. Original
results and screenshots are retained; each was observed by GET only afterwards.

| Batch | Publications | Operation ID | Domain run ID |
| --- | --- | --- | --- |
| 1 | 32 | ec64615d037e566ce511be8019a1c4a9 | 2be13ea0644b4c04aa2f2c2bfd269354 |
| 2 | 32 | 81da4f9ec7723572693418ac5bf90acd | 530b295213364348b887f80746a16889 |
| 3 | 32 | 3eca2adc2c6a07421968e2675a557ca2 | 33ea0fe1d6e64f08b5cc2848d70bf237 |
| 4 | 32 | 3af49d9c91a562eaae2ed32b56c0a7e3 | b057fef7c2054d1ea32ee6ac487ffc1b |
| 5 | 27 | 2ee65600db9bbf7235489abed20939d3 | d2ab2b2b30c146c3b261fe16e2bde002 |

Independent actual installed SDK reads freshly bind all156 observations to exact
original manifest hashes/generations/timestamps. All156 raw manifest bytes and
both historical prune journal bytes are unchanged; current refs/232 retained
publications/verification inventory compare exactly. Original12 operation-store
bytes/inodes and permanent retirementb5217fb9 are unchanged. Counts:7 complete,
27 partial,8 unsupported,114 failed interpretations; zero observation-write
failures. Every149 incomplete record has exact diagnostics and an actionable
handoff, primarily configured work/read/source/header limits and unsupported
formats/dtypes. Unknown optional fields stay unknown; no weights downloaded or
loaded, integrity promotion, larger budgets or cleaner-report replay. No second
backfill is authorized by this completion.

Protected evidence under
`/opt/hfcache/deployment/20261105-job-recovery-0.3.4/`:

| Receipt | SHA-256 |
| --- | --- |
| release-preparation1/backup1.json | c35fcc9e5ba814fa5e2fa4a22677bcfc7a18a6199374bd5db94e6b2c948c24bf |
| release-preparation1/drain1.json | eb1ba640198cac3430c68821527965bccad7866472d5bced6c720c7e21ecdf64 |
| stage1/result.json | 7fcccee7fcb663d4bd5236120c2b6d41f3f3dd0915688c89b768ab74b1a3f8c1 |
| writer-select-bind1/result.json | 402f117f9076c07411b8509911755aa1acce975903ebb0529b99d8fe2a1ccec4 |
| writer-resume-rw1/result.json | f885aeb2ed6bf1c5cd1060ff5cef4da52028ff704db798bee886decb175fc4f1 |
| writer-start1/result.json | 1fcca26d0d7866b3300f7fee460bf1216abb39c24a9cc67e345eb4b789af35e0 |
| writer-installed-preflight1/result.json | 014ae06cb4ca7c1dab4ead0db3364e84be857015f435ffffd658d3a8957cf9bb |
| selected-pilot-checkpoint1/result.json | 7ac0214cea563c72d26c2db7ca4ea04e8bb94e0948d3a1490ad2c7277d30080d |
| backfill-final-acceptance1/result.json | e6a0ca95d8c650b0ecdaa5807b8e9bd7f636eb6c6ed8d7884ad6a43a8787c964 |
| backfill-final-acceptance1/incomplete-observation-actions.json | 0e257d50c22d77034f0779ee50559633957b56c62c0c685f184b32bf883bcfe6 |
| final-host-observation1/result.json | 6c739daa7d61d97e5aad7969a9aaccf35b7bebd172f3c0bdc2fa7126607964c6 |

The failed observer reports and original metadata failure are preserved. User.env
credentials were parsed as data/in memory, never logged/staged/copied into these
artifacts; original user browser storage remains untouched. Original uncommitted
draft SHA2b823aae remains exact. No pushes/tags/registry publication, init, manual
archive writes, reboot/disconnect/NAS change/other-host action occurs.

Final technical inputs, including the repaired supported-SDK NFS test helper,
pass OPS029 default gate9935/backend/build/three profiles (12d17fdf,1358.63s)
and REL020 strict gate9948/backend plus all strict web/browser/build/profile
checks (79c38bf1,1671.58s/1287 frozen inputs unchanged). Six selected read-only
actual NFS checks pass2.20s; application production jobs are separate evidence.
Only factual documentation changed after the strict gate. Final focused
documentation alignment passes217 human documents/29 helpers;69 focused checks
pass8.11s. Raw log `cd08f419f8b427dd2e9c9585e01ead52538e418e7918fdbcdde28bb8497f5cbe`;
private NAS shadow/login1000. The first factual docs check correctly refused
public links to internal task records; public evidence now lives directly in
deployment status. Original failed docs log is preserved.

Reviewed FS02/19/21–23, AD16/17, TX03–07, INV003/007/018/020/021/023 and
ADR121/150/159/164/165/166. Existing contracts/decisions govern these actions;
no new authority, dependency, durable format or decision is introduced. Human
container/recovery/deployment guides and current host checkpoint are reconciled.
Enforcing/kernel policy, original locks/engine metadata/credentials/predecessors,
disabled calendars/masked writers and inactive guard/bridge are freshly proved.
Manual current-boot startup and compatible drained guarded rollback remain the
supported scope; unattended boot, NAS settings, other-host/all-phase companion
and unrelated maintenance/configuration workflows remain independent holds.

### Historical execution notes

The following dated checkpoints retain their original scope; completion evidence
above owns the final state.



2026-11-05 dependency preparation only: OPS028 guarded startup and automated
actual read-only acceptance pass; genuine existing administrator original-record
recovery is pending. This task remains pending. The coordinator prepares the
finite validation/transition scope and one bounded application-reader revision
inventory independently; no writer selection, mount/grant change, Hub request,
Sync, refresh or metadata backfill is executed here. The scoped production
instruction supplies write/pilot authority after all safety prerequisites;
password authentication and fresh measured transition facts are still required.


Read-only installed revision inventory now succeeds, response SHA256
`3374953abce678695391d8bbdf5ebb32cd5b4349e7b2a2d784d3c64d54754c28`,
104944B. It returns156 repositories with232 retained publications; each156
current references joins exactly one retained manifest/publication. Protected
candidate/batch record
`fab161171c7266e31fded16d8488b4b09a1ff8bbe1b4ddd02cb2ff09834f04a6`
proposes32/32/32/32/28 current-publication batches, within per-request caps, with
fresh budget/identity/eligibility checks still required before effects. Smallest
configured enabled candidate: model:Cudecnik/Qwen3.8-Flash-Next-refusal-projection,
1030096B/eightfiles/one retained revision; next google/gnm-v3,53345971B/fivefiles/
one retained. These are candidates only; no upstream query/Sync plan, capacity
or retention readiness is inferred. No job, Hub request, writer selector, RW
mount, grant change or archive write occurred. Genuine OPS028 completion remains
the dependency; do not advance this task from pending yet.


Installed reader status for the smallest pilot candidate succeeds without a job,
response SHA256 `37e065cb9d3336ca2652cd573cc2f93515977d57f04c9b6e44e10cb90ee77a3e`,
1614B. Actual archiveUUID matches configuredf2a38add; available10419078955008B,
reserve3864245305344B and headroom6554833649664B. Unfinished transactions0,
unknown entries[], outstanding verification failures0. One explained existing
quarantine finding1af6a7b0 remains untouched; no cleanup is inferred or authorized.
Candidate current1886570b/generation1 is managed/enabled with one retained
revision; verification remains unverified and upstream state unknown. These are
current guarded read-only observations, not writable-mode/mapped-ownership or
upstream target/retention preflight. No Hub lookup, job POST, mount/grant/profile
change or archive write. Further effect prerequisites await genuine OPS028
administrator recovery; independent bounded inventory/candidate/capacity
preparation is now recorded and does not need repetition while awaiting input.

2026-11-05 activation: OPS028 completes actual guarded0.3.3 installation,
genuine administrator UI review/retirement and disabled-job explanation checks.
Original request is permanently retired_unknown, historical uncertainty retained,
zero job replays. Credentials are authorized and authenticated; no human auth
block remains. Select this task for fresh writer-specific backup/drain and
original-lock handoff. New immutable writer indexa638f833, guardedf1c55ed2,
source1652b8f/app661da09f/UIc9df46e1. Existing inventories remain preparation,
not writer proof; recheck actual limits/identity at effects. No writer effects yet.

2026-11-05 actual writer transition in progress: fresh coherent backup705edb6a/
full API-first drain35d55b87, writer selection and measured binding2bb5565d,
local persistent remount829920b8 all pass with original guards. Archive grant
remained false through inert namespace maintenance. Installed vendor Podman
6.0.2-1.el10 no-option migrate executes once after real drain/private coherent
SQLite backup; old1953/birth889 namespace is empty/retired and original pause
inode63:60 retained. Upstream-predicted conmon changes were not performed by the
vendor binary: actual full DB bytes/schema/rows unchanged, verification1d2671ea
passes without repeat. New keeper434678 authenticated through one normal info,
user4026532694/mnt4026532695/maps0->981/1->589824 and actual NFS RW view,
receiptf830eb1c. Engine lock/SHM original inodes/labels preserved, bodies unread.

Independent archive-only false->true grant and ordered helper/worker/API/Caddy
receipt6715fe87 passes; index8cc9f9a4/policyc1356315, other grants unchanged.
Original guard/bridge inactive, calendars disabled/native writers masked,
Enforcing. Actual writer SDK read-only storage preflight passes both application
roles, UUID/config165/retention3/reserve3864256000819B, available10419185909760B,
receipt d2535e93. Worker IP socket is denied ENOSYS under actual confinement;
initial observer omitted ENOSYS from its expected errno set, failure retained,
no policy change or SDK repetition. Original retirement/stores/credentials remain.
No Sync/refresh/backfill job has run at this point.

Finite NFS validation scope: six existing read-only mount/sentinel/staging/skip/
no-write assertions in tests/system/test_live_mount.py; no mutating health probes,
init, Hub or CLI/API job from the test runner. That opt-in suite still invoked
retired local --config doctor syntax; adapt its subprocess helper to the supported
application storage SDK, preserving actual kernel-mount assertions and separate
guarded application path for unselected mutating cases. This is test-only; actual
installed rootless preflight/pilot acceptance remains separate. Required default
repository gate follows this source edit; no repeated strict web/release matrix.

2026-11-05 actual selected sizingdd09e42f and Sync943f7560 succeed through genuine
installed administrator UI. Reviewed upstream1886570b is current,1030096B/eight
files, zero new bytes, one retained/max3; Sync skips up-to-date, downloads/prunes
nothing and preserves publicationb4d95efd/gen1. HFWRN011 remains accurate. Genuine
technical-refresh4050dbaa/run a8ec217e is admitted then fails HFVER007/exit40.
Original result/handles retained, no automatic retry/replay. Read-only actual
CatalogWriter diagnosis narrows refusal to checkpoint-order validation of two
committed2026-07-26 prune journals. Their raw hashes and old producer5dc8d0a^
prove valid original10-step shape, missing only next-day containers_removed.
Never edit/delete/rewrite those archive records. Necessary REL020 now selected;
this task is blocked only on that source/artifact dependency, not authentication.

Read-only actual six scoped NFS checks pass2.20s after supported SDK test helper
repair. OPS029 default gate1 result will retain its exact scope; it is not the
new compatibility release gate. Genuine backfill inventory156 current/232retained
and3327465B exact manifest API projections is prepared with32/32/32/32/28 proposed
batches, no job submitted. Root-protected checkpoint0a233d0b preserves sizing,
Sync, failed refresh, screenshots and full inventory. Original12 store files and
permanent original retirementb5217fb9 retain exact bytes/inodes. No backfill or
metadata acceptance is claimed. Current writer state/Enforcing/masks/grants remain
as above pending fresh protected deployment of the compatibility release.

2026-11-05 REL020 strict release gate and matching immutable0.3.4 artifacts pass;
resume this task. Fresh backup/full real drain and original-lock handoff precede
a temporary connected RO install window, both official stages and writer
selection/exact labels/measured matching helper binding. Preserve current writer
grants and persistent override; restore actual RW and revalidate the existing
434678 namespace before ordered helper/roles. No extra activation or migrate.
Fresh affected current-version sizing/Sync validates the changed supplemental
journal guard, then a distinct new explicit metadata pilot after fresh GET of
original failed4050dbaa. One bounded backfill reuses that exact pilot observation,
five UI batches32/32/32/32/27 cover155 remaining; raw156-manifest prebaseline
74067423 is retained for exact postcomparison. No automatic replay. The earlier
156-current API projection baseline and root checkpoint remain authoritative.
