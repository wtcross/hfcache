# Restore manual Sync and metadata refresh with understandable job recovery

| Field | Value |
| --- | --- |
| Status | active |
| Created | 2026-11-03 |
| Authorization | User instruction 2026-11-03: implement all eight packages, protected local deployment, controlled writer transition, selected pilots and bounded backfill after safety prerequisites |
| Execution model | `gpt-6.1-sol`, with explicit per-task effort below; no implicit client default |
| Tracker | [Current plan](current.md); this plan is selected |
| Starting source | Clean `main` at `7fceb8d`; recorded deployed application source `c23abba`, release 0.3.1 |

## Outcome

An administrator can run a manual Sync or refresh technical metadata on this
host, understand why an action is unavailable, and recover from a lost response
without managing keys, inspecting JSON, or accidentally repeating work. Existing
archive evidence and operation history survive the change.

The user has activated all eight work packages and narrowly authorized this
host's protected local deployment, controlled writer transition, selected pilots
and bounded backfill after the safety prerequisites. Task records already exist
and the current selector owns execution order. No remote push, release tag,
registry publication, automatic schedule, other-host action, reboot, NFS
disconnection, NAS change, manual archive write or archive initialization follows
from this authorization. The verbatim original draft remains preserved separately.

## Findings and constraints

1. Sync and catalog refresh both require protected `archive` permission before
   admission. The observed policy has `archive=false`, while configuration and
   Hub permission are true. The archive is mounted NFS read-only. Legacy native
   sync services/timers and the verification calendar are masked/inactive.
2. The browser also blocks all new jobs for an unresolved original request. The
   reported record is `762c47c1147542ce82edbceb0b7bd327`, for
   `/api/v1/catalog/refreshes`, under Basic subject `archive-admin`, with key
   `695b24c7-437d-42ed-a91f-39dbc0cb58c7` and no operation ID. Browser recovery
   storage is ready. A bounded host-local scan found five receipts, no matching
   Basic-subject key, no catalog-refresh receipt, and no active receipt at the
   time checked. The first HTTP response is unavailable; permission rejection
   is a plausible explanation, not proven historical nonexecution.
3. Every post-transmission API problem currently leaves a browser record
   uncertain. A subsequent missing-history response cannot release that block.
   Missing history alone must continue to mean unknown. Restored completed
   records also require fresh observation, currently exposed as manual recovery.
4. Rootless source currently enforces read-only operation: API/worker archive
   binds and startup checks require it, the helper's rootless mount inspector
   rejects `nfs-rw`, and the installer requires a read-only selection window.
   The archive label and Enforcing policy need actual writer qualification.
   Changing one permission flag and remounting is insufficient.

Evidence sources: [current deployment](../../deployment-status.md),
[route authorization](../../../src/hfcache/api/host_authorization.py),
[browser submission gate](../../../web/src/state/session-controller.ts),
[recovery registry](../../../web/src/state/operation-registry.ts),
[rootless launcher](../../../scripts/container-service.py), and
[host inspection](../../../src/hfcache/host_policy.py).
Re-observe host facts before execution; this list is investigation evidence,
not a live-state reservation.

## Scope and product behavior

- Show a reason beside each unavailable job before submission, for example
  **Sync unavailable: archive writes are disabled**. Distinguish permission
  denial, read-only storage, unavailable readiness, an active job, and a request
  needing review. A disabled button must have an accessible explanation.
- Use existing authenticated permission/readiness evidence where possible.
  Load it through bounded reads when Jobs opens or its context changes; provide
  explicit recheck after failure. Evidence is advisory, scoped and invalidated
  on authority changes. The server still authorizes every submission freshly.
  Optional host-read permission must not become an additional authorization
  prerequisite; use independently available action grants and label unobserved
  facts unknown without claiming the action itself was denied.
- Present ordinary states such as **Checking**, **Unavailable**, **Submitted**,
  **Running**, **Completed**, **Failed**, and **Needs review**. A completed
  failed job remains an admitted job with its original result. An admission
  refusal is a different state and must not suggest work is running.
- Keep tracking keys, raw receipt states and JSON in advanced diagnostics.
  Routine recovery offers one contextual action with the original job name,
  observed outcome, and next step. Preserve nonsecret handle export.
- Reconcile saved original requests automatically with bounded authenticated
  GETs on a visible, freshly authenticated page. No automatic POST, implicit
  retry, cancellation, permission change, or response-loss replay. Amend the
  current deliberate-observation/visibility policy explicitly before changing
  it; hidden pages stop polling and late responses cannot donate fresh proof.
- Restore manual jobs only. Keep automatic calendars disabled, legacy native
  writers masked, rootless schedule/observer permissions denied, and unrelated
  control permissions unchanged. Manual Sync does not require enabling timers.
- Retain the current metadata extractor and its supported fields. This work
  does not add Hugging Face model-info enrichment, model execution, parameter
  counts, or context-length extraction.

## Accepted recovery design

WEB-031 accepts [the executable recovery contract](../../job-recovery.md),
[decision 164](../../adr/decision-164.md) and
[decision 165](../../adr/decision-165.md). These choose the finite protocol and
writer scope below; source and installed acceptance remain with the later tasks.

Introduce a separately versioned, bounded, server-owned original-intent
disposition in protected local control state. Bind it to the archive, existing
authenticated key namespace and route; retain no raw credential, raw key or
replayable request body. Use the same cross-process serialization as admission
so a receipt and a closed key cannot race into contradictory authority.

For a fresh validated request rejected before admission, durably retain an
explicit rejection/fence before returning a typed **Not admitted** response.
If that key already has a receipt, preserve and observe the original receipt;
a later permission denial cannot redefine an earlier accepted request. Every
future admission checks the fence and refuses execution under a retired key.
An arbitrary 403/404/503, malformed reply, transport failure or client assertion
is insufficient proof. Failure to persist the disposition remains uncertain.
Retired keys must not become executable through receipt expiration, disposition
cleanup, restart or an older-binary rollback. Bounded storage refuses new work
at capacity unless safe compaction preserves the fence; an older binary that
cannot enforce it must not regain admission authority.

For the existing key-only record, provide authenticated recovery review which:

1. Looks up the original Basic namespace and returns any existing admission.
2. Establishes fresh actual executor/worker state and checks pending protected
   effects. It must not treat a free flock, client exit, absent receipt, current
   denial, or a browser-supplied route as proof that historical work never ran.
3. When no original active work or unresolved protected effects can remain,
   permits an explicit reviewed retirement of that original intent. Persist the
   fence, scope, review evidence and **Historical outcome unknown; request
   retired** disposition. Preserve the original browser record and its handles.
4. Allows distinct new intent after fresh verification of that disposition,
   while never reporting old success/nonexecution or replaying the old request.
   Configuration/host outcomes retain their independent confirmation rules.

Specify the race-free execution/admission interlock, evidence freshness,
authorization, bounded retention, crash behavior, corrupt-state refusals and
rollback readers in the contract task. Protected helper exchanges must not run
under the operation-store lock. If execution ownership or protected effects
cannot be established, retain **Needs review** with a concrete operator action;
there is no generic dismiss-unknown button or browser-storage deletion remedy.

This is a proposed architectural change. It requires an ADR and explicit
amendments to the current recovery rules, rather than reinterpreting a missing
receipt as permission to clear a record. Preserve schema-1 browser evidence
through an explicit versioned migration and an old-reader compatibility drill.
Define a least-privilege authorization path for the original administrator's
own intent recovery while archive, schedule, observer and unrelated control
grants remain denied. Recovery must neither require enabling those grants nor
confer authority to execute a new archive job.

## Writable runtime and production transition

Define an explicit independently protected rootless writer profile, with the
existing guarded read-only profile remaining the default. Bind the selected
mode to immutable runtime/index and helper authority; no browser toggle, generic
mount selector, executable override or ambient environment grants writes.

Implement consistent role mounts, startup checks and helper recognition of
`nfs-rw`. Grant only application role/path writes required by the existing
Sync/refresh and verifier-persistence contracts. Preserve worker network/secret
isolation and helper/observer payload neverallows. Inspect the actual archive
label and prove required transactional writes under SELinux Enforcing; no
label-disable, NAS relabel/chown/copyup, privileged container or broad helper
payload grant. Unknown profile/mount/guard facts fail closed.

Keep the installer's drained NFS-read-only stage/switch/rollback window. Design
an explicit reversible transition between that window and running writer mode,
including the independent guard's system/bridge dependencies, original lock
handoff, persistent local mount override, and helper-before-API startup. Preserve
the deliberate guard setting outside the transition. Resolve current boot-time
runtime provisioning/helper ordering for the writer profile, or provide a
verified fail-closed manual startup procedure and clearly limit acceptance to
the current boot; do not infer unattended boot support.

Before effects, take a fresh protected coordinated backup/inventory of config,
candidates, old artifacts, secret identities, both operation stores, helper
outcomes/dispositions, browser handles and original lock inodes. Confirm no
unknown active work. Stop admission and drain the API while the private worker
can report outcomes, then drain worker/helper/inspector cohorts. Prove actual
process/cgroup/libpod quiescence and retain the original noncreating flock.
Stage/select matching immutable artifacts while NFS remains read-only; refresh
protected bootstrap/index/policy/SELinux bindings before starting the helper.

The authorized write transition must separately prove the existing writer
host/export, mapped ownership, exact sentinel UUID, writable NFS identity,
capacity/reserve, and application preflight. Do not run archive initialization,
create manual archive probes, disconnect NFS, change NAS policy, reboot, or
weaken SELinux/systemd confinement. A missing prerequisite is an explicit stop
condition. No automatic replay or automatic rollback after an uncertain effect.

Rollback stops admission, drains real executors and helper cohorts, reacquires
the original lock, restores NFS-read-only plus the reviewed policy/guard state,
and selects a compatible retained release. Preserve all new state and a
compatible recovery reader. Application rollback does not undo archive changes
or restore publications removed by normal Sync retention.

## Model and reasoning effort

Use `gpt-6.1-sol` for implementation and review. Use `medium` for coordination,
bounded UI implementation against the accepted contract, executing an established
validation matrix, and release assembly. Use `high` for the recovery protocol,
durable concurrent state, writer confinement, and production state transitions.
These are workload-based starting choices, not a claim of benchmarked optimality.

The local Codex model catalog was checked on 2026-11-03: it exposes both `medium`
and `high` for this exact model and currently defaults to `low`. Specify effort
explicitly. The [official effort guidance](https://developers.openai.com/api/docs/guides/deployment-checklist#set-up-reasoningeffort)
supports medium/high for diagnosis, planning and code reasoning; higher effort
is not a reason to expand task scope. [Codex model controls](https://learn.chatgpt.com/docs/models)
describe selecting the model and effort in the client.

At activation, verify the actual session/agent settings and copy the task's
model/effort into its execution notes. A Markdown table does not change runtime
settings. Where available, use one task agent with explicit
`model="gpt-6.1-sol"` and the assigned `reasoning_effort`; an override-capable
fresh-context agent gets the task, relevant contracts, current evidence and file
ownership, rather than the entire historical transcript. Do not silently inherit
`low` or claim to have changed the coordinator's settings without actual control.
If the client cannot apply a setting, identify that setup limitation before
using a different model or effort. Avoid spawning new agents merely to watch
commands, copy logs or repeat an already completed review.

Escalate a medium task to `high` only for a named reproduced defect or unresolved
lifecycle/security decision. Escalate `high` to `xhigh` only for a specific
remaining race or conflicting safety evidence after a focused high-effort
attempt; record the question, new evidence sought and resolution, then return
to the assigned level. Do not select `max`/`ultra`, switch models, benchmark
effort levels, or create a model-tuning work package for this plan. Effort
escalation never authorizes additional tests or unrelated work by itself.

## Work packages

The task records below were created at activation and own execution status and
evidence. Default execution is sequential; concurrent implementation requires
explicit task ownership and nonoverlapping file scopes in the active records.

| Order | Work package and future task file | Depends on | Model / effort | Required result |
| --- | --- | --- | --- | --- |
| 1 | WEB-031 — [web-031-job-readiness-and-recovery-contracts.md](tasks/web-031-job-readiness-and-recovery-contracts.md) | None | `gpt-6.1-sol` / `high` | Contract-first state/UX design, disposition and legacy recovery protocol, writer-profile scope, invariant/ADR amendments and finite acceptance matrix; stop design when these decisions are executable |
| 2 | API-019 — [api-019-original-intent-dispositions.md](tasks/api-019-original-intent-dispositions.md) | WEB-031 | `gpt-6.1-sol` / `high` | Bounded durable rejection/fencing and authenticated reconciliation; preserved admitted jobs, Basic namespaces and unknown historical outcomes, with focused race/crash/authorization tests |
| 3 | WEB-032 — [web-032-job-readiness-and-automatic-recovery.md](tasks/web-032-job-readiness-and-automatic-recovery.md) | API-019 | `gpt-6.1-sol` / `medium` | Accessible job availability reasons, bounded GET-only recovery, clear refusals/results, advanced diagnostics and preserved schema-1 handles; use the accepted protocol rather than redesigning it |
| 4 | OPS-027 — [ops-027-explicit-rootless-writer-profile.md](tasks/ops-027-explicit-rootless-writer-profile.md) | WEB-031 | `gpt-6.1-sol` / `high` | Supported protected writer runtime, role mounts/startup/helper/SELinux changes, read-only defaults and reversible selection procedure; qualify changed authority boundaries |
| 5 | WEB-033 — [web-033-job-recovery-and-writer-acceptance.md](tasks/web-033-job-recovery-and-writer-acceptance.md) | API-019, WEB-032, OPS-027 | `gpt-6.1-sol` / `medium` | Close named acceptance gaps using direct installed job/recovery workflows and the affected format/profile drills; reuse valid unchanged evidence and update human guides, without building a new harness |
| 6 | REL-018 — [rel-018-job-recovery-writer-release.md](tasks/rel-018-job-recovery-writer-release.md) | WEB-033 | `gpt-6.1-sol` / `medium` | Clean committed source and reproducible immutable matching backend/UI/image/helper artifacts; documented rollback compatibility using existing release tooling |
| 6a | REL-019 — [rel-019-original-review-journal-accounting.md](tasks/rel-019-original-review-journal-accounting.md) | REL-018 | existing coordinator | Necessary actual-host conformance fix: count at most1024 fully validated journals with separate enumeration/read accounting; prepare matching immutable0.3.3 release, preserving the original eight-package acceptance scope |
| 7 | OPS-028 — [ops-028-install-job-recovery-release.md](tasks/ops-028-install-job-recovery-release.md) | REL-018 and REL-019 | `gpt-6.1-sol` / `high` | Guarded local installation while NFS stays read-only; actual Basic/UI/helper negative-permission behavior and reviewed recovery of the reported key |
| 8 | OPS-029 — [ops-029-enable-manual-archive-jobs.md](tasks/ops-029-enable-manual-archive-jobs.md) | OPS-028 and recorded production-write/pilot authority | `gpt-6.1-sol` / `high` | Controlled writer transition, selected real metadata/Sync pilots, one bounded backfill of existing current publications and final operational handoff |

No push, release tag, registry publication, schedule activation, other-host work,
or unrelated backlog is selected by this active plan. These are explicit retained
user boundaries; do not extrapolate an earlier rollout exception.

## Execution focus and validation boundaries

The finish line is functional manual jobs and understandable recovery on the
selected deployment. Neither a larger test framework nor a perfectly uniform
historical evidence collection is a deliverable.

1. Before implementing each task, record a finite table in its existing task
   file: changed requirement, smallest meaningful behavioral check, required
   gate, and evidence/result. Reuse existing tests, logs, screenshots and task
   evidence formats. Add a row only for an actual changed requirement, reproduced
   defect or uncovered safety clause; record why. Do not create a new collector,
   evidence schema, report binder, fixture manager or acceptance framework.
   WEB-031 chooses the smallest change to the existing operation/store/runtime
   machinery that meets the stated guarantees, records that decision, then
   advances to implementation. Do not turn the fix into a generic workflow
   engine, permission-system redesign, new frontend stack or architecture study.
2. Start with the task's product behavior. Run focused checks while iterating,
   then the mandatory gate for that implementation commit. Once scoped checks,
   required gates and evidence pass, complete the task and advance. Additional
   runs require a relevant source/artifact/environment change, observed failure
   or named unresolved requirement. Full source hashes changing do not imply
   that every unchanged subsystem needs fresh behavioral qualification.
3. The standard gate remains mandatory, including its existing harness and
   strictness checks. Do not skip a failing stage, weaken assertions or relabel
   a failed command as passed. A single successful strict gate can satisfy the
   default gate for the same commit; do not run the default gate again solely
   to obtain another log. Do not execute the slow full suite after every minor
   edit or repeatedly rerun a green gate on unchanged final inputs.
4. Harness changes are allowed only for a reproduced blocker preventing one of
   the named product checks or a mandatory gate from running truthfully. Use
   the smallest repair, with a direct reproducer and the affected stage. Do
   not add tests of test generators/collectors/drivers, generic harness
   hardening, new fault frameworks, or recursive tests of those repairs. Source
   pins, generated protocol fixtures and assertions may be updated when actual
   changed product semantics require it; retain their validation strength.
5. After two harness-only attempts at the same failure without new evidence,
   stop repeating that approach. Record the failure, command, hypothesis and
   missing evidence; choose a narrower reproducer or the existing direct
   installed acceptance path if it satisfies the same contract. If a mandatory
   stage remains blocked, report it honestly and continue independent scoped
   work. This is a strategy-change checkpoint, not permission to waive checks,
   abandon a product defect or declare the whole plan complete.
6. Use **Installed product workflow acceptance** in
   [development](../../development.md#installed-product-workflow-acceptance).
   Direct actual Caddy/TLS/API/browser/worker/helper observations are required
   for changed installed behavior. The optional `--with-web-functional`
   instrumented runner is outside this plan's execution path. Do not invoke
   that flag or its `--final` protocol, provision its 95-case/18-cell matrix,
   repair its old reports, or extend it for a new aggregate. Preserve its code
   and existing mandatory source-stage tests; direct installed acceptance must
   retain truthful product/security evidence instead of claiming a runner pass.
7. Respect the installed-profile/browser clauses in the development contract.
   Reuse earlier passing evidence only with its original scope and an explicit
   unchanged-code/behavior/environment justification. Exercise changed shared
   browser/API behavior in the affected supported profiles; rootless writer
   changes need actual rootless positive/negative checks, not a new native
   runtime feature. Do not multiply every race/crash/security test across every
   browser and prefix when its required layer is the store or runtime boundary.
8. Name the exact affected previous-release reader and changed durable format
   before a compatibility drill. Prove the new dispositions/recovery migration
   and writer-profile rollback behavior; do not qualify every historical
   release or replay predecessor rollouts. Retained
   [test-release evidence](../../web-ui/test-release-acceptance.md) and old
   progress/handoff records supply context, not a new backlog or an instruction
   to rerun all acceptance. Boot, other-host, all-phase companion, unrelated
   maintenance/configuration workflows and optional performance work stay
   outside this plan unless an actual changed boundary requires a named check.
9. Production pilot jobs and metadata backfill are effects owned by OPS-029,
   executed once and observed by their original handles. They are not fixture
   setup or repeated regression gates. A warning or incomplete capture requires
   inspecting the original result before deciding on any separately scoped
   follow-up; never resubmit merely to obtain a cleaner report.
10. Status updates name the work package, user-visible behavior proved, remaining
    named check and next action. After interruption/compaction, resume from
    recorded evidence and task status instead of restarting setup or rerunning
    completed tests. Apply the same scope rules to delegated agents and reviews.

## Acceptance and validation

1. With archive permission disabled or storage read-only, the UI explains the
   specific observed reason and sends zero job POSTs. Missing/unavailable or
   stale readiness is explicit. Permission changes between read and submission
   remain enforced by the server and produce recoverable typed outcomes.
2. A confirmed pre-admission rejection stays rejected across reload/reconnect,
   never becomes a phantom running job, and does not strand unrelated new
   intent. Admission versus fence races, duplicate keys after permission
   changes, crash/fsync failures, expiration/capacity and corrupt/future state
   have deterministic preserving behavior. Test non-revival after retention,
   compaction and restart, plus the affected previous-release reader selected
   in the task's compatibility matrix. No all-history binary matrix is needed.
3. Lost acknowledgements after real admission recover the exact original job
   and result using reads only. Test Basic rotation with the same subject,
   another subject/bearer namespace, cross-tab edits, hidden pages, API restarts,
   storage failures and malformed responses. Verify exact POST counts and no
   replay. Unknown configuration/host effects cannot be cleared by generic
   job recovery.
4. The reported old record has an installed supported recovery path without
   deleting handles, fabricating nonexecution, or rerunning its request. Its
   historical uncertainty remains visible if an original receipt cannot be
   recovered. Ordinary users can complete the workflow without copying keys
   or editing JSON. Genuine ambiguity still has a useful operator action.
5. Guarded defaults refuse writes; explicit writer mode works in actual owned
   installed fixtures. Prove changed mounted role rights, shared original lock,
   helper binding, affected neverallows and Enforcing writer behavior, plus
   identity/capacity refusals, drained restart and rollback. Preserve unchanged
   verifier network/secret isolation and cite valid baseline evidence; rerun
   the affected checks if its execution boundary changes. Disposable local
   fixtures do not count as actual NFS writer acceptance.
6. After separately authorized deployment/write transition, observe one selected
   technical-refresh result and one selected Sync through genuine administrator
   UI and original API results. Review the pilot repository, current upstream
   target, capacity and installed retention effects before Sync; do not start
   all 165 selections as the first test. Retain manifests, publications,
   warnings, journals and operation/run identities as appropriate.
7. Backfill current publications in enumerated bounded batches, honoring the
   256-repository/512-publication refresh caps and shared extraction/write
   budgets. Every eligible publication has a bound observation or an explicit
   actionable capture failure. Partial/unsupported evidence remains accurately
   labelled; missing optional fields cannot be presented as known. Refresh
   does not download weights, load models or raise integrity confidence. This
   backfill is the single scoped OPS-029 execution, not a recurring test step.
8. Run focused API/store/profile tests and built real-browser workflows for the
   changed behavior, including keyboard, screen reader labels, narrow layout
   and zoom. Each implementation commit passes `rtk scripts/check.sh`; web
   changes additionally pass `--require-web`. Release acceptance passes
   `rtk scripts/check.sh --require-web --with-build`. Complete direct installed
   product-workflow acceptance for the changed behavior and the format/previous-
   binary drills selected for changed durable domains. The optional instrumented
   shared-Caddy runner is not a release prerequisite for this plan. Keep a
   finite missing-clause list rather than expanding acceptance after success.
   Build/gate as the login user with the live archive excluded from fixtures.
   Run opted-in NFS tests only within the later recorded production scope;
   Hub live tests are required if the Hub adapter changes.
9. Update human operations/recovery/deployment/rollback guides, current host
   checkpoint, task evidence and progress in their respective implementation
   commits. Report actual writer state and remaining independent acceptance
   holds. Manual jobs work while automatic schedules and unrelated permissions
   retain their scoped settings.

## Contracts and decisions to maintain

- [Planning](../planning.md), [workflow](../workflow.md),
  [record policy](../technical-record-policy.md), [environment](../environment.md)
  and [release/format drill](../release.md).
- [Invariants](../../invariants.md): FS-02, FS-19, FS-21–23, AD-16/17,
  INV-003/004/005/010/013/014/015/018–022. Amend the read-only deployment and
  pre-fetch-only browser recovery rules explicitly; retain archive identity,
  no-replay, immutable evidence and protected-effect boundaries.
- [API admission](../../api.md#admission-idempotency-and-lifecycle),
  [server](../../server.md), [schemas](../../schemas.md),
  [security](../../security.md), [offline discovery](../../discovery.md),
  [job/recovery guide](../../web-ui/operations.md),
  [administration](../../web-ui/administration.md),
  [container profiles](../../containers.md), and
  [drain/rollback](../../deployment-centos-stream-10.md#upgrade-and-drain).
- Review/amend the applicable portions of ADRs
  [114](../../adr/decision-114.md), [115](../../adr/decision-115.md),
  [118](../../adr/decision-118.md), [126](../../adr/decision-126.md),
  [127](../../adr/decision-127.md), [141](../../adr/decision-141.md),
  [145](../../adr/decision-145.md), [146](../../adr/decision-146.md),
  [150](../../adr/decision-150.md), [154](../../adr/decision-154.md),
  [159](../../adr/decision-159.md), and [162](../../adr/decision-162.md).
  Record new decisions for durable intent disposition and rootless writer
  authority; allocate decision numbers during implementation, preserving prior
  rationale and explicit supersession links. Do not add runtime dependencies.

## Lifecycle

- 2026-11-03: Draft written at the user's request after read-only investigation.
  `current.md` remains unchanged with no active plan. No implementation task,
  deployment, host permission change, archive job or production write is started.
- 2026-11-03: User requests explicit `gpt-6.1-sol` effort by task and safeguards
  against harness-testing loops or unrelated work. Add the model/effort table,
  actual-setting verification, evidence-based escalation and finite validation
  rules. Replace the unnecessarily required optional instrumented runner with
  the existing direct installed product-workflow path, preserving mandatory
  gates and changed-boundary safety tests. The plan remains draft-only.

- 2026-11-03: Activated by explicit end-to-end implementation authority. The
  original uncommitted draft is preserved verbatim in
  [original-draft.txt](support/job-recovery-and-archive-writes/original-draft.txt),
  SHA-256 `2b823aae1a8b18c01f019a75a46587a9cbeae88ec4ea8cf2d36367ca04fa491b`.
  All eight task records created before implementation. Production authorization
  narrowly supersedes prior read-only restrictions for the planned actions; all
  prerequisites and prohibitions remain. No push, tag or registry publication.
  Coordinator runtime settings are not changed or inferred; task execution uses
  fresh-context agents with explicit model/effort controls from this plan.

- 2026-11-03: WEB-031 specifies the executable finite recovery/writer contract,
  ADR164/165, INV023 and the downstream acceptance matrix. No implementation,
  host mutation or installed writer acceptance is inferred. API-019 is next
  after the mandatory contract commit gate.

- 2026-11-03: Preserve the verbatim original draft as .txt: relocation leaves
  its relative Markdown links invalid for the repository-wide Markdown link
  gate. Exact bytes and SHA-256 remain unchanged; no test assertion is weakened.

- 2026-11-03: WEB-031 completes its contract/ADR/invariant design and finite
  acceptance handoff after the passing default gate and separately scoped
  post-gate focused documentation checks. The next selected task is API-019.
  No implementation or installed writer acceptance is inferred. Retained draft
  bytes/hash are unchanged; only known successful new gate fixtures retire
  after reviewed complete inventory and fresh no-owner proofs.

- 2026-11-03: API-019 completes bounded disposition1, generic Job refusal/reconciliation,
  shared/exclusive execution leases, actual worker/helper review and narrow offline
  selected-runtime activation. Gate25 passes9644 backend checks, package/three
  locked profiles and all required strict web/source-browser/read-fixture stages
  with1276 unchanged frozen files. Reviewed source contracts retain fixed protected
  effect authorization/outcome precautions and historical refusal causality.
  Full failed payloads/logs remain preserved through reviewed exact current-temp
  retirement; no production state or writer mode changes. WEB-032 is next; its
  browser and later installed/renderer acceptance are not inferred.


- 2026-11-03: WEB-032 completes accessible readiness/recovery, atomic browser2
  migration, causal saved refusals and authenticated bounded GET-only reconciliation.
  Explicit reviewed retirement preserves original handles and independent protected
  effects; unknown history never becomes replay authority. Strict gate3 passes9644
  backend/3809 unit/4169 combined/16 built browser/actual200% zoom/real API React
  checks with1279 frozen inputs unchanged. Both failed prior gates and full payloads
  remain preserved; exact count corrections retain strict source authorities.
  OPS-027 is next. Source completion is not installed/runtime/writer acceptance;
  no deployment, live archive/service/permission/mount change, tag or push occurs.


- 2026-11-03: OPS-027 completes protected guarded/manual-writer runtime2 and
  immutable manifest2 siblings, independent helper/domain joins, original-lock
  drained NFS-ro staging, fixed offline real-parser intent activation/companion
  provisioning and preserving current-boot transition/rollback procedure. Default
  gate19 passes9711 tests, package build and three locked profiles with1281 frozen
  names/hashes unchanged. Failed gate10/full payload and all policy diagnostic
  failures remain preserved. Owned current-boolean binary/AV compatibility is
  bounded source evidence; strict Enforcing workloads/native transient/mounts and
  actual NFS writer proof remain WEB-033/OPS-029. No production state changes,
  deployment, tag or push. WEB-033 is selected next.

- 2026-11-05: WEB-033 closes actual native/rootless recovery, permanent-fence
  compatibility and isolated activation, Enforcing rootless application writes,
  original-lock waiting, storage negatives, missing-companion refusal/restoration,
  drained restart and compatible guarded RO rollback with original evidence intact.
  Strict gate12 passes on final technical inputs; factual closeout uses focused
  documentation checks. Existing unchanged decoder/browser evidence is reused
  with explicit scope. REL-018 is selected next. Production deployment, original
  historical-key recovery, selected pilots and bounded backfill remain pending;
  no production completion follows from the owned fixture.

- 2026-11-05: REL-018 completes0.3.2 release source and matching reproducible
  backend/UI/helper/app artifacts, immutable mode inputs/renders and final-image
  foundation. Strict gate4 passes9929 backend and all required web/build stages,
  including16 wheel smoke cases. Three named fixture defects are repaired with
  assertions retained; failed gates/candidates remain. Exact source2d4c9cc is
  retained independently of the final evidence commit. Existing unchanged worker,
  Caddy and WEB-033 compatibility/workflow evidence retain their explicit scopes.
  OPS-028 is next; protected production stages/deployment, genuine old-key
  recovery, writable transition and scoped pilots/backfill remain pending.


- 2026-11-05: Actual OPS-028 retirement reaches full protected review after
  documented host-history provisioning, then exposes a source work-accounting
  defect:621 resolved JSON journals/2875196B exceed a1024 shared enumeration+
  read budget despite fitting the byte limits. Add necessary release follow-up
  REL-019 before completing OPS-028. This corrects bounded journal accounting
  and supplies immutable0.3.3 artifacts; every original eight-package criterion
  remains. User authorizes genuine administrator credentials in ignored.env;
  no credential contents, original job replay, format change or new grant.

- 2026-11-05: REL-019 completes bounded journal accounting and matching clean
  immutable0.3.3 artifacts. Strict gate passes9935 backend/all strict web/build
  stages with1284 frozen inputs unchanged; focused red/green and limit tests
  retain whole-history refusal and byte bounds. Unchanged worker/Caddy proofs
  retain their original scopes. OPS-028 resumes fresh protected deployment and
  actual original-key UI retirement; original eight criteria remain in force.

- 2026-11-05: OPS-028 completes actual guarded0.3.3 installation after fresh
  protected backup/drain/original-lock handoffs. Matching helper binding/ordered
  startup and installed29-case checks pass. Genuine administrator installed UI
  reviews/retires original key as retired_unknown with historical uncertainty,
  handles and original12 store bytes/inodes preserved, zero job replay. Genuine
  disabled Sync/refresh UI and authenticated helper/config GETs pass. OPS-029
  activates for fresh controlled writer transition/pilots/one bounded backfill;
  production still NFSRO/Enforcing/archivefalse. No full-plan completion claim.
