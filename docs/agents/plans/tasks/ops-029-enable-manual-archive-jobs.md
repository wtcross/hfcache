# OPS-029: Controlled writer transition, selected real metadata/Sync pilots, one bounded backfill of existing current publications and final operational handoff

| Field | Value |
| --- | --- |
| Status | in_progress |
| Plan | [Job recovery and archive writes](../2026-11-03-plan-job-recovery-and-archive-writes.md) |
| Depends on | OPS-028 and recorded production-write/pilot authority |
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
