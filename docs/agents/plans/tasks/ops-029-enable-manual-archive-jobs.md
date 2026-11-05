# OPS-029: Controlled writer transition, selected real metadata/Sync pilots, one bounded backfill of existing current publications and final operational handoff

| Field | Value |
| --- | --- |
| Status | in_progress |
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
| Writer transition prerequisites | Completed genuine OPS028 recovery; fresh original configuration/store/disposition/credential/artifact backup and complete actual executor/helper drain; same original flock handoff | `scripts/check.sh` plus actual protected receipts | OPS028 complete; fresh writer-specific backup/drain next |
| Guarded-to-writer selection | Select already qualified writer sibling while NFSRO; exact index/runtime/source/image and matching helper authority/grants | Same gate plus official switch/retained originals | Matching0.3.3 sibling staged/indexa638f833; not selected |
| Local mount and namespace transition | Reviewed persistent local mount override/remount without disconnect; proc1 and retained rootless namespace identity/rights; fully drained normal namespace handoff if stale | Actual current-boot mount/namespace receipts; original locks/guard preserved | Current host and pause namespace NFSRO; no turnover or RW remount |
| Actual writer preflight | Application sentinel UUID, exact writer host/export, mapped ownership, reserve/capacity, Enforcing role rights, helper READY before ordered roles | Installed application read-only preflight and fixed role/confinement checks | Pending writer selection; no manual write probe or init |
| Selected genuine UI/API pilots | Review one repository/upstream target/size/retention effects, then one distinct new Sync and one technical-refresh request; retain exact original operations/results/run/publication evidence | Actual administrator browser workflow and API original results | Genuine administrator authenticated; writer preflight and pilots pending |
| One bounded metadata backfill | Enumerate current publications; finite batches within256-repository/512-publication/shared extraction budgets; every eligible publication bound or explicit actionable failure | One authorized execution with retained inventory/operations/results/coverage evidence | Read-only preparation only; no refresh/backfill submitted |
| NFS scope and final handoff | Only required opted-in application NFS checks within approved scope; actual writer state/rollback and remaining independent holds documented | Scoped NFS result, repository gate, factual docs checks, WP commit | Pending; no interruption/disconnect/NAS-side effects |

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

Pending. Source and unit tests alone do not establish installed acceptance.


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
