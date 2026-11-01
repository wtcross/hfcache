# WEB-022: Prove full installed functionality on isolated native and rootless targets

| Field | Value |
| --- | --- |
| Status | completed |
| Plan | [Web UI replacement](../2026-10-20-plan-web-ui.md) |
| Phase | P5 |
| Depends on | [WEB-021](web-021-immutable-ui-release-packaging.md) |
| Branch | `feat/web-ui` |
| Work-package commit | `WEB-022: prove installed native and rootless functionality` (this commit) |

## Governing acceptance amendment 2026-11-01

The user explicitly adopted the [product-focused proposal](../../../../.scratch/web-022-validation/web022-proportionate-acceptance-proposal.md):
“i accept the new proposal”. Its criteria now govern this task and final acceptance.
Only the mandatory normal-runner85×18/95×18 cross-product and acceptance path are
superseded; earlier requirements/results remain historical evidence. All95 underlying
product/safety behaviors and clauses remain required, with an explicit missing-test
list and no missing clause marked passed. Use appropriate unit/integration/direct
installed actual-UI evidence; retain Chromium/Firefox/WebKit on native/rootless at
root/management. Deeper fault/profile cases run once where the relevant boundary
exists. Preserve original operations/failures and justify reuse by unchanged subsystem
scope; the full repository source gate is unchanged. The later dependent tasks are
still pending; this amendment is not task completion or production/NAS acceptance.

## Read before implementation

Strict final functional gate and fixture runner; artifact indexes from WEB-021; complete parity/acceptance matrices; actual guest hardening checks.

Also read the relevant sections of [architecture](../support/web-ui/architecture.md), [API contracts](../support/web-ui/api-contracts.md), [testing strategy](../support/web-ui/testing-strategy.md), [acceptance matrix](../support/web-ui/acceptance-matrix.md), and [human documentation map](../support/web-ui/documentation-map.md). Load only affected living contracts and ADRs through their indexes. Refer to the [source review](../support/web-ui/source-review.md) for pinned baseline evidence; current git wins over it.

## Scope and implementation requirements

Run the full application and platform functional profiles using exact installed release artifacts, trusted private TLS and real browsers. Rootless uses actual Podman/systemd identity/manager boundaries and native uses actual bound system units; keep guests and state disjoint from production. Capture peer, service, cgroup, socket, asset and secret visibility evidence from running processes, not only template inspection.

Exercise every required UI workflow including real config application, card read/capture, original operation recovery, worker verification, all maintenance fixture effects, positive supported schedule/observer behavior and guarded rootless denials. Existing CLI bearer reader/writer and fourteen read-only MCP tools operate through the same Caddy concurrently. Test missing/unsafe config/helper, late permission drift, lost response/process interruption and drains with evidence preserved.

Fix discovered defects with scoped tests and recorded work-package boundaries; split follow-up packages if needed without editing completed evidence. A missing browser/image/guest/network isolation resource blocks this task; do not redefine component fixtures as platform acceptance. Do not run live Hub or NAS tests to compensate.

## Unit and component validation

Full backend/frontend/unit/component gates remain green; trace any installed failures to new regression tests. Validate acceptance evidence structure and required test-to-case links.

## Integration validation

Run all new integration suites plus existing CLI/HTTP/Unix/worker/MCP regressions and safe release install checks on the selected artifact source. No skipped required suite.

## Functional validation

Execute the full repository gate with `--require-web --require-cockpit --with-build`
and reconcile all85 cases owned through this package under the governing
2026-11-01 amendment. Direct installed native/rootless evidence must include
Chromium, Firefox and WebKit at root and `/management`, with deeper fault/domain
checks at the relevant boundary. Record exact artifacts, browsers, guest setup,
exits and assertions; later-owner cases remain pending. The existing runner,
`--require-through` and `--with-web-functional` are optional diagnostics whose
strict protocol remains unchanged, not commands claimed by this acceptance.

## Human documentation deliverables

Correct deployment/troubleshooting guides from the installed walkthrough. Add a human-readable test-release acceptance summary that explicitly excludes production rollout/NAS proof.

## Acceptance

Real installed native/rootless functional acceptance is complete with no mock-only parity claims or skipped prerequisites; evidence identifies exact artifacts and the limits of the proof.

The task also requires the existing `scripts/check.sh` gate plus strict applicable web/Cockpit and functional checks described above. New capabilities are not completed solely by adding test descriptions. Update actual test-to-case mappings and run them. Documentation and relevant contract/invariant/ADR updates land with the behavior, not in a later catch-up task.

## Execution notes and blockers

### Checkpoint 2026-11-01: Accepted installed coverage and required source gate complete

The resumed reconciliation preserves every original execution and required layer.
All85 cases owned through this task are complete in the existing ledger; ten
later-owner cases remain pending. Retained individually passing clauses and
read-only qualifications are distinguished from original failed aggregates.
No accepted Apply, maintenance, Repair, schedule or observer effect was replayed.
The one uncovered actual password-rotation clause now has a real protected-file,
Argon2-provider and durable-store integration test; its focused66 tests and full
Gate21 pass. Runtime source remains the installed f829857e/0.2.78 candidate.

Gate21 inner/outer both exit0;9646 backend/4051 combined frontend/581 Cockpit/
16 wheel checks, three locked install profiles, two built-browser checks and
real API HTTP fixture pass. All1545 frozen inputs remain unchanged. Required
gates run as loginUID1000 with the live NAS hidden by an empty read-only private
mount. Subsequent changes adopt acceptance/closure records only, with separate
documentation/plan/diff validation. Full evidence and qualifications follow in
the completion section; earlier checkpoint states are historical.

### Checkpoint 2026-11-01: Fresh-session execution resumed

The user's execution goal resumes the paused plan and this in_progress task.
Git still selects feat/web-ui at WEB-021/2c44f2d; all existing uncommitted work
is retained, including the untracked root dependency directory. Gate20's frozen
runtime/test files match current bytes; only acceptance/handoff documents have
changed since that gate. Root coordinates all protected/guest/browser effects.
Three disjoint read-only audits reconcile AUTH-01–07, ROUTE-02/03/06 and
HOST-10/RELEASE-04 against actual retained files before any new product test.
No accepted operation is replayed and no historical failed aggregate is changed.

### Checkpoint 2026-11-01: User-requested pause and fresh-session handoff

After accepting the product-focused proposal, the user requests a safe stopping
point and pause. Plan paused; task remains in_progress/acceptance incomplete.
The [fresh-session implementation prompt](../support/web-ui/fresh-session-implementation.md)
and [copyable goal](../support/web-ui/fresh-session-goal.md) authorize later
resumption. Accepted criteria remain adopted; the prior decision blocker is
resolved, not awaiting another answer. No ledger edits were made:73 completed,
12 unfinished through this task (AUTH-01–07, ROUTE-02/03/06, HOST-10, RELEASE-04).
Reconcile retained actual evidence first; add a check only for a concrete
unproved behavior. Preserve all original exits and scope, no accepted-effect replay.
All source-only agents released their files; no gate/browser/job was started
after adoption. Gate21 launchers are prepared/unrun with no TMPDIR or final
freeze; Gate20 remains the last full passing gate. Adoption contracts and handoff
receive one inexpensive documentation/plan validation before the goal is paused.
No commit, new runtime behavior, production effect or future-task activation.
After completion, apply the refreshed13-document testing/effort amendments before
WEB-023. Current implementation/proof details remain in the retained checkpoints.


### Checkpoint 2026-11-01: Acceptance proposal adopted; task continues

User approval: “i accept the new proposal”. WEB-022 returns to **in_progress**,
plan active; the required decision blocker is resolved by explicit adoption, not a
default waiver. The governing amendment above supersedes the historical mandatory
normal-runner matrices while retaining every product/safety clause, missing list,
original ID, failed result and honest installed-evidence scope. No clause becomes
passed solely through adoption. Tool goal status still reports blocked and the API
has no resume method; no tool-resumed claim is made. The user authorizes continued
task work. Root updates the related normative documents separately. WEB-023–026
remain pending; future13-document effort/testing patch2 stays unapplied until AFTER
WEB-022/BEFORE WEB-023. No new framework/schema, test, guest or runtime action here.

### Checkpoint 2026-11-01: Blocked on required acceptance-basis decision

Final prepared outcome: **blocking decision required; goal blocked**. This is the
third consecutive genuine impasse (audit13 count1, audit14 count2, current turn
count3): no acceptance-basis reply/adoption, and the original normal-runner85×18
through this task/95×18 final requirements remain unchanged. Product-progress
checkpoint12, Gate20 and all current78 positive/failed-run evidence remain intact.

Unblock only when the user either adopts the prepared [proportionate acceptance
proposal](../../../../.scratch/web-022-validation/web022-proportionate-acceptance-proposal.md),
which retains every product/safety behavior and marks no missing clause passed,
OR explicitly authorizes the necessary runner implementation to retain the original
matrix. Additional easy/read-only subset passes cannot satisfy the mandatory normal
runner. Do not repeat passed checks or enter HTTP-observer/test-machinery loops.
There is no default scope waiver, acceptance pass, commit or future-patch application.
The plan remains active, not paused; WEB-023–026 stay pending and future13-document
patch2/efforts remain unapplied. VM fixtures, original operations and user data stay
preserved. Root will set and verify the blocked goal outcome after the record check;
no tool-return claim is made by this prepared checkpoint. Earlier entries retain
their historical status and observed results.

### Checkpoint 2026-11-01: Rootless Administration denial visibility passes

[Host-denials1](../../../../.scratch/web-022-rootless-fixture4/rootless78-host-denials1-result.json)
`3a2bd481` passes transport/browser0/121.763s/six cells/12callbacks, all three
browsers × both prefixes. Bootstrap/Administration/actual HostControls UI shows
guarded/guard-held/NFS read-only, config granted; archive guard-held, Hub/control
policy-denied and schedule/observer profile-unproved. Text matches actual current
HostStatus/ObserverDTO. Edit Sync Schedule/Review Original Observer disabled,
Stop absent, Verification Timer read-only heading visible. Actual button+browser
status/observer reads are GET-only; no POST/job/operation/config/service effect.
Strict page/console/CSP/5xx/external/nonGET/violations0/all contexts/browser/server
closed; cancellations[5,4,0,0,0,0] retained. All five preservation proofs pass:
same confined roles/original1790 guard/NFSRO/seven publications/currentdf9/29disabled/
history/SDK/credentials/old browser. Rootless stops0/smoked407d495; native remains
stopped0/6a681b7e. Reviewed source/carrier52448e68 runs once, no new VM/build/framework.
This proves denial VISIBILITY only, not backend mutating refusal/full HOST-08/
family/matrix. All owned browser/test executors are terminal; no more work this turn.
Dataset/README/Gate20/worker/MCP/config/status/futurepatch2 facts stay unchanged;
overall INCOMPLETE/WEB-022 in_progress/original requirements unchanged/optional scope
unanswered/023–026 pending. One cheap record validation remains for Root.

### Checkpoint 2026-11-01: Dataset detail scope passes with retained continuation

[Rootless1](../../../../.scratch/web-022-rootless-fixture4/rootless78-dataset-detail1-result.json)
`10e0d8b0` remains raw1/51.035s: Chromium root+management each pass three callbacks;
Firefox/root stops only on supplemental response-event[401] versus expected[404],
while actual in-page browserRead is404/nonHTML. All five preservation proofs/closures
pass/no effects. Only that supplemental event equality is removed; actual fetch404/
nonHTML, exact URL diagnostics and strict other health stay required, events retained.
No HTTP observer/auth diagnosis loop. [Rootless2](../../../../.scratch/web-022-rootless-fixture4/rootless78-dataset-detail2-result.json)
`033f2297` passes0/75.452s/browser0, ONLY remaining Firefox/WebKit four cells/12callbacks;
Chromium is not rerun. [Native2](../../../../.scratch/web-022-fresh-fixture2/native78-dataset-detail2-result.json)
`fcf279a3` passes0/110.729s/browser0/six cells/18callbacks; native dataset1 is prepared
but UNRUN. Rootless scope joins retained two Chromium cells plus four fresh cells;
its original aggregate stays failed.

Both profiles bind exact fixture/data SHA40/publication32 ending0015, two files/
319 B, attributed dataset_config/feature/split/format paths/digests/values, no model
or inferred metrics, explanatory text, Files bytes/SHA/locator bases, rawfetch404/
nonHTML and reload/back-forward retaining the same pinned pair. Unexpected console/
page/CSP/5xx/external/nonGET/violations0; all contexts/browser/servers close. Expected
exact raw404 resource diagnostics are qualified only in Chromium/WebKit; Firefox's
401 event versus in-page404 remains. Cancellation counts retained: native[12,13,2,6,6,6],
rootless2[5,4,4,6],rootless1 Chromium[12,8], not zero failed requests. Native whole
preservation passes including SDK95048553/1722free/roles/NFSRW; rootless all five
proofs include29disabled/df9/seven publications/guard1790/NFSRO/roles/SDK/keys.
Both stop0/common smoke `6a681b7e6cf671c08170ed9cedf3fadccea2a54ca7d2d5364cf218eecf28a06e`.
No new VM/build/framework/operation or repeated passed Chromium. This is selected
dataset coverage, not full CATALOG-07/08/family/matrix. Gate20/README48/currentworker/
MCP/CONFIG-12 facts unchanged; Library cause unqualified/optional scope unanswered/
original85×18 unchanged/WEB-022 in_progress/023–026 pending/futurepatch2 unapplied.

### Checkpoint 2026-11-01: Retained README card-state UI passes

[Native states1](../../../../.scratch/web-022-fresh-fixture2/native78-card-states1-result.json)
`f540f7b6` passes transport/browser0/117.086s/six cells/24 callbacks;
[rootless states1](../../../../.scratch/web-022-rootless-fixture4/rootless78-card-states1-result.json)
`fdfcd805` passes0/111.886s/six cells/24 callbacks. Each Chromium/Firefox/WebKit ×
root/management cell checks bootstrap; generations1 unsafe(secret_suppressed),
2 unsupported,3 unsafe fail closed with no source/active DOM; generation4 refuses
deep formatting while exact9413 B sanitized source remains/no clobber; generation5
shows table/code/image placeholder, protected HTTPS/new-tab links with noopener
noreferrer/no-referrer, pinned relative guide and no active DOM/clobber.

Strict page/console/CSP/5xx/external/nonGET/violations0; all contexts/browser/servers
close. Request cancellation diagnostics remain native[6,5,2,2,2,1] and rootless
[8,7,1,2,2,2], not zero failed requests. No operation/POST/config change/job. Native
whole preservation passes, including SDK95048553/same roles/1722free/NFSRW;
rootless all five proofs pass: seven publications/currentdf9/29disabled/history/
SDK/credentials/helper/same confined roles/guard1790/NFS read-only/old browser originals.
Both existing CIDs stop0 with common actual smoke
`7cfc165d950cdb39a3f2d9cb1645fa4eb9e282231877c1b1c46ebeafb967b7d7`.
Existing browser image reused; no VM/build/framework. Root-reviewed carriers
293f67a7/93e9bd95 execute once each. These selected retained-state successes grant
no full CARD-12/CATALOG-08/family/matrix stamp. Original Library lookup remains
unqualified despite ONE successful query; no diagnostic loop. All Gate20/worker/
MCP/CONFIG-12 facts unchanged; WEB-022 in_progress/original85×18 unchanged/optional
scope unanswered,023–026 pending/future13-document patch2 unapplied/high-medium-high-medium.

### Checkpoint 2026-11-01: Query loss not reproduced in one bounded attempt

[Query1](../../../../.scratch/web-022-fresh-fixture2/native78-library-query1-result.json)
`3792865a` passes0/17.513s, native Chromium/root/two callbacks, strict health0/
closed/preserved. Exactly ONE attempt/nine bounded passive events: q=fixture/model
at input, after fill and actual submit; settled expected URL and one matching row.
No late pageshow/hashchange/popstate occurs after input. Query loss is NOT reproduced
once; original Native1 lookup remains failed/cause UNQUALIFIED. This is no fix or
resolution claim and no further diagnostic loop is planned. Native stops0/smoke
`0050e5a333ae9f182819beb2169f3b67c8d734f50f8d1994ae449c630f17938a`;
rootless remains stopped0/9c0eeebe.

Both owned [native](../../../../.scratch/web-022-fresh-fixture2/current78-card-states-readonly1.json)
`c61b282c` and [rootless](../../../../.scratch/web-022-rootless-fixture4/current78-card-states-readonly1.json)
`49ce7b9a` metadata collectors exit0: retained generations1 unsafe(secret_suppressed),
2 unsupported,3 unsafe,4 present/deep9413 B,5 present481 B; all publication pairs
match references. No capture/payload read/change. Existing-fixture fail-closed card,
deep-format and link-provenance actual-UI gaps are source-prepared, NOT executed;
no new fixture/VM/harness framework follows. Current12-cell README/Files/native78
worker/MCP/CONFIG-12/Gate20 facts stay unchanged; no full-case/matrix stamp.
WEB-022 in_progress, optional scope unanswered/original requirements unchanged,
023–026 pending/future13-document patch2 unapplied/high-medium-high-medium.

### Checkpoint 2026-11-01: Current README/Files pass in native and rootless

[Native2](../../../../.scratch/web-022-fresh-fixture2/native78-rich-card-files2-result.json)
`e60ce316` passes transport/browser0/81.759s, six cells/12of12;
[rootless1](../../../../.scratch/web-022-rootless-fixture4/rootless78-rich-card-files1-result.json)
`8db31b1f` passes0/79.122s, six cells/12of12. Both actual current model fixtures have
TWO manifest files, not the separate eight-object worker scope. Assertions bind
exact model publication pair/f829/0.2.78/UI578, manifest/card/README/presentation
identities, inert DOM/sentinels, pinned relative guide/blank/noopener noreferrer,
exact sanitized source and Files counts/byte values/digests. All12 cells have strict
page/console/CSP/5xx/external/nonGET/violations0 and all contexts/browser/servers close.
Retained aborted-request counts in reported cell order: native[7,2,1,1,2,2],
rootless[3,6,2,2,2,2]; no request-failure-zero claim. No new operation/Apply/job.

Native whole archive/API-worker/config/SDK pending/bound roles/global1722/NFSRW/
old browser originals remain exact. Rootless all five proofs pass: seven publications,
current29/df9 configuration/application history/SDK/credentials/helper/same container
roles/guard1790/NFS read-only. Native stops0/smoke
`e2222a0e742b9ff090c78549ed1d26e4e77b0786ffd3212c3ee021abeb48ab81`;
rootless stops0/smoke `9c0eeebe27355799fde5888b5c213ea82988979883d396d4dbeb96ca050e5322`.

[Native1](../../../../.scratch/web-022-fresh-fixture2/native78-rich-card-files1-result.json)
`5bb8a5d5` stays raw1/41.162s at the first Library target anchor after bootstrap:
URL lacks q/default search,31 matches/25 rows; closed/preserved/health0/no POST.
Cause is UNQUALIFIED: conditional late readLocation draft overwrite exists in source,
but no trigger was observed; neither product-bug nor harness-only attribution follows.
Native2 reaches the exact publication by deep link with unchanged original assertions.
One bounded actual UI query-loss probe is source-prepared, not executed; no further
diagnostic loop is planned. These are scoped CURRENT README/Files passes, not full
CARD-12/CATALOG-08/all-scenario/matrix acceptance. Gate20/current worker/MCP/CONFIG-12
facts stay unchanged; WEB-022 in_progress, scope unanswered/requirements unchanged,
023–026 pending/future13-document patch2 unapplied/high-medium-high-medium.

### Checkpoint 2026-11-01: Genuine native78 revision worker and MCP report

[Worker1](../../../../.scratch/web-022-fresh-fixture2/native78-revision-worker1-result.json)
`1779478a` stays outer1/39.056s on an overstrict lock-mtime/ctime collector assertion;
browser0/5of5 proves visible exact-SHA form/permission, ONE POST202, genuine0.2.78
clean report, same-original reload and unchanged exact publication/manifest/last-full.
Operation `5a4d8703327836302d722708537d08ab` MUST NEVER repeat; record2690b3c2,
domain run `a9e3697b62514830b78b0961bc6ab1e1`, report
`runs/20261101T062340Z-a9e3697b62514830b78b0961bc6ab1e1.json`. Scope1 repository/
1 revision/8 objects/6286 B, SHA9×40/publicationed17/generation3.
[Read-only qualification1](../../../../.scratch/web-022-fresh-fixture2/native78-revision-worker1-readonly-qualification1-result.json)
`04dd2f88` passes0/1.569s: matching API+worker operation succeeds/new record pairs,
durable0.2.78 report joined, only the new run report/scoped verification catalog
update. All old API-worker records/publications/unrelated catalog/config/credentials/
SDK pending95048553 and same four roles/global1722 free/NFS read-write remain.
Only global lock mtime+ctime change through normal holder write/truncate;
inode/owner/mode/label/empty SHA/size0 stay exact. Raw outer failure is preserved;
no job rerun. Browser retains19 `net::ERR_ABORTED` diagnostics, including accepted
POST; page/console/CSP/5xx/violations0/all closed. Request failures are NOT zero.
Native browser stops0, smoke `b4193f339c272f688936fce1a090fc479b46ea7c188757a58bf57a9aa3742fa2`.

[New-report MCP reads](../../../../.scratch/web-022-fresh-fixture2/native78-revision-report-mcp1-result.json)
`39b8a777` pass0/5.319s: exactly two `get_verification_report` reads at root/management,
joining persisted SHA `da066416516486b1e5efafdb49156bc459fc83bad8e0ca055020129b355251e6`;
report comparison excludes only contract-separated findings, entries=findings=[]
match. No new job; API-worker record bytes/report/SDK pending unchanged. These reads
are separate from the earlier9UI+32-client overlap, which used old0.2.75 reports;
no concurrency with this new worker or rootless/full-matrix claim follows.
Prior overlap-record checks pass docs222/29 helpers, plan9 and diff0; they predate
this update. CONFIG-12/Gate20/status unchanged: WEB-022 in_progress, optional scope
unanswered,023–026 pending/future13-doc patch2 unapplied/high-medium-high-medium.

### Checkpoint 2026-11-01: Native UI/client overlap qualifies

[Overlap2](../../../../.scratch/web-022-fresh-fixture2/native78-client-overlap2-result.json)
`73611ddb` passes transport/browser/client0/42.979s; [qualification1](../../../../.scratch/web-022-fresh-fixture2/native78-client-overlap2-qualified1.json)
`052f7b3a` verifies all nine existing visible Library filter intents on native0.2.78
Chromium/root. All four CLI reader/writer status calls and28 MCP calls (all14 tools,
both aliases) pass. All32 call intervals fit fully inside actual UI workflow
1793513607874–1793513644256ms; clients1793513617985.155–1793513642748.7605ms,
with40 actual UI API requests during the clients. Strict health0/all browser/client
actors closed. Archive/API-worker stores/config/SDK pending95048553/credentials/
old browser originals/native bound roles/original1722/loopback NFS read-write stay
preserved. Native browser stops0, smoke `b5ed6c64c4fcfee330416c7fe8c40b2c270bb3206dd29113c57fd85c463ac7f1`.

[Overlap1](../../../../.scratch/web-022-fresh-fixture2/native78-client-overlap1-result.json)
`b4b30cf7` remains raw1 before READY/clients: wrong API-header assertion on UI
bootstrap CSP; browser closed/old world unchanged. Only that assertion changes,
not runtime. This qualifies actual native browser/client concurrency, not rootless
concurrency, a new worker/report or the full matrix. Existing genuine0.2.75 full/
revision reports are read exactly. Scoped CONFIG-12/Gate20/retirement facts remain
unchanged; WEB-022 in_progress, optional scope unanswered/requirements unchanged,
023–026 pending and future effort patch2 unapplied. Human summary now distinguishes
this native overlap from sequential rootless reads; overall acceptance INCOMPLETE.

### Checkpoint 2026-11-01: Scoped CONFIG-12 add/remove continuation passes

[Continuation6](../../../../.scratch/web-022-rootless-fixture4/rootless78-configuration-human6-result.json)
`335c8e20` passes transport/browser0/152.825s and12/12 callbacks: no errors, console,
CSP,5xx or violations; all browser actors close. Earlier continuation5 `99fce5b4`
remains raw1/first8 pass: same-original add recovery before/after reload, exact30/
protected fields/publications and both new Library rows pass; only removal
Validate200 runs before Preview correctly refuses until another restored original
preview is freshly verified. This is legitimate safety, not a product defect.

Continuation6 restores EXACT actual human4 storage, observes BOTH original
previewe611 and Addc00/host, then performs only the new removal: Validate200,
empty Preview202 `867ad8ec38f00af5ec08c0776d95a63b`, ONE Apply202
`21f81fd4609c79f0fde586fdbe1e0277`, host confirmed/pending=false. Final configuration
`df9b4a7c6a0ca7c09833864b22f4fe162d5bcc8da5aa6663d42769c53da10d74` has29 entries,
all disabled. Exact before/after documents, only2 new operation file sets/1 new
application directory, predecessor/raw30/older backup chains and actual installed
fingerprint all pass. Seven publication trees/refs/manifests/cards/observations,
old operations/histories/worker/SDK/credentials/browser originals and confined
roles/helper/guard1790/NFS read-only remain unchanged. Removed dataset is unmanaged,
**Tags not observed**/[] because its historical snapshot was absent; its pinned
publication pair stays exact. NEVER repeat Addc00/removal21f or prior1dc/74c.

Direct scoped add/remove assertions now pass across retained failed attempts and
this passing continuation. Older aggregates remain failed; no single full20,
full CONFIG-12 family or matrix stamp follows. Gate20/retirement remain unchanged;
WEB-022 **in_progress**, optional proposal unanswered/requirements unchanged,
023–026 pending and future effort patch2 unapplied. Overall acceptance is INCOMPLETE.

### Checkpoint 2026-11-01: CONFIG-12 add succeeds; workflow remains incomplete

Preflights1/2 (`97157de7`/`20617db1`) fail before staging on inactive-timer PID fields
and absent fixture/data historical-tag snapshot. Browser3 `f6801eee` then fails
before any POST on unavailable Playwright response body, closed/all preserved.
[Browser4](../../../../.scratch/web-022-rootless-fixture4/rootless78-configuration-human4-result.json)
`b19649b3` remains raw1: first8 callbacks pass; the ninth compares the new config
fingerprint to old preview/startup evidence after real model+dataset forms,
Validate200, empty Preview202 and Apply202. This is a test comparison error,
not a product bug. Add Apply `c00f41e4b2bf4d2d63f6afadae90658d` succeeds with
host confirmed/pending=false and exact candidate. [GET-only original observation](../../../../.scratch/web-022-rootless-fixture4/config12-add-original-observation1.json)
`997d9d2a` confirms configuration `759ed9f4de1d4b748fc1ad12e32327833277dcce8e06ef79ad061d1ae3671e3e`,
30 disabled entries. NEVER replay this Apply or prior1dc6b7fd/74c9794a.

All three preservation claims pass: seven publications/archive observations;
old operations/application histories/worker/SDK/credentials/browser; same confined
roles/helper/guard1790/NFS read-only. Read-only original recovery/exact30 and only
the previously unsubmitted archived-dataset removal are being prepared, NOT run.
CONFIG-12 remains incomplete; no full20 or matrix pass. Gate20 green and successful
TMP-retirement facts below are unchanged. The [future13-document patch2](../../../../.scratch/web-022-validation/web023-026-bounded-product-testing2.prepared.patch)
`b189fe19` is prepared, unapplied, with high/medium/high/medium task efforts.
WEB-022 remains **in_progress**; optional scope proposal unanswered/requirements
unchanged, WEB-023–026 pending. No new validation or protected action accompanies
this record update.

### Checkpoint 2026-11-01: Gate20 passes; product acceptance remains open

[Gate20 inner](../../../../.scratch/web-022-validation/gate20-result.json) `fa2b6d86`
and [outer](../../../../.scratch/web-022-validation/gate20-shadow1-result.json) `2596cc63`
pass0/1723s:9645 backend,4051 combined frontend,581 Cockpit,16 wheel, three locked
profiles, two built-browser checks and real HTTP; all1543 frozen files unchanged.
This is the latest full green source gate, not normal85×18 installed acceptance.
Completed TMP retirement0 (`/var/tmp/web022-gate20-temp-retirement1/result.json`,
`48f3300c`, prepared8339591) retains183016-entry inventory/extents,13 finite outputs
and two passing all-UID reference checks. Root free612728832→1566720000 B, measured
gain953991168 B. Interrupted Gate19 TMP, all VM fixtures, originals and user cache remain.

Newly explicit CONFIG-12 gap: normal configuration's28 read/edit/refusal callbacks
and13 conflict callbacks do NOT add a model and dataset. The prepared20-callback
actual-UI helper is unexecuted: add disabled model+dataset/Apply30, then remove
archived fixture/data configuration/Apply29 while preserving all seven publications.
These are original product tests, requiring no acceptance-scope amendment. Neither
prior Apply1dc6b7fd nor74c9794a may be replayed. One bounded stock-role branch
implementation attempt is scratch-only; no schema/runtime/boundary weakening or
passing stock-lifecycle evidence follows. Full13/AUTH-05/normal85×18 remain open.
WEB-022 stays **in_progress**, not blocked on the unanswered optional scope proposal;
requirements remain unchanged. WEB-023–026 stay pending and their13-file effort
patch remains unapplied. The human summary reports source-gate success but INCOMPLETE
product acceptance. Root prepares the next actual UI run; none is claimed here.

### Checkpoint 2026-11-01: Separate read-only navigation and B recovery

[Follow-up2](../../../../.scratch/web-022-rootless-fixture4/rootless78-management-navigation-followup2-result.json)
`d008066c` passes0/23.266s, companion stdout `8fd667b6`: independent fresh LOCAL
unsaved draft→**Discard draft and leave**, then a separate context restores the
EXACT actual B export `configuration-conflict-rootless-prefixed-chromium-B-storage-final.private.json`
(`a8f479e5`). SAME B-preview6c8b/original recorda6d8/result survives reload; SAME
stale local9508/key remains without an operation ID. This does not reconstruct the
old RAM actor. No POST/forbidden/error/console/CSP/5xx; all contexts/browser/server
close, config bytes/API-worker-application record names stay exact and pending absent.
Follow-up1 failed before browser staging on the wrong export filename; only the two
filename/output scopes change. Original Management1 `44eaab74` remains raw1/40of41;
no all41/full13 same-run or normal-matrix pass is inferred. Neither Apply repeats.

Same-attempt Firefox Podman logs and unit journal both read0/empty. Its header/body
mismatch stays unqualified AUTH-05; no further form/log/infrastructure work starts.
Gate20 is the next required full check. Overall acceptance remains INCOMPLETE; user scope
proposal is unapproved, WEB-022 in_progress/023–026 pending and future patch unapplied.

### Checkpoint 2026-11-01: Management conflict and interrupted gate

[Management1](../../../../.scratch/web-022-rootless-fixture4/rootless78-configuration-management1-reuse-result.json)
`44eaab74` remains raw1, with40/41 callbacks passing: actual UI stale409/conflict
comparison, new A-Apply `74c9794a906b4f2eaf098cf4b894b079` confirmed and original
recovery. The last B→Operations navigation meets the legitimate unsaved-draft dialog;
this is a test-guard error, not a product defect. [Read-only effect qualification](../../../../.scratch/web-022-rootless-fixture4/management1-actual-effect-readonly1.json)
`43c10d4c` proves current configuration `b3fa6294`, predecessor `03349448`, only the
new prefixed tagA added,28 disabled/pending=false. Prior root Apply `1dc6b7fd` stays
retained: NEVER repeat either Apply. Driver `f4d5585a` now explicitly chooses
**Discard draft and leave**; formatting closes0. Focused read-only B storage export/
restore/recovery is still being prepared, with no new POST; full13 remains unproved.

[Gate19 inner](../../../../.scratch/web-022-validation/gate19-result.json) `b5f23dbb`
and [outer](../../../../.scratch/web-022-validation/gate19-shadow1-result.json) `079a5be7`
end2 after one ordinary SIGINT to the owned pytest:1953 passed/52 deselected,
all1542 sources unchanged/all six known PIDs absent. Logs/TMP remain; this is not
green. Gate20 is prepared, NOT started; Gate18 remains the latest full green gate.

[Firefox multipart1](../../../../.scratch/web-022-rootless-fixture4/rootless78-firefox-multipart1-result.json)
`9ff5c86a` remains raw1: both observations complete healthy/closed, source sockets
drained and config/record names unchanged, but401 headers and403 body IDs mismatch.
AUTH-05 stays unqualified; no more form reruns. The fresh leaf issuance passes0
(`8e264764`), without CA/trust/product changes. Podman logs read0 but empty; any
journal follow-up is observation of that same attempt, not a new request.
The [human test-release summary](../../../web-ui/test-release-acceptance.md) and web
index link now explicitly state INCOMPLETE. Normal85×18 and full13 remain open;
user scope decision is unanswered, requirements unchanged, WEB-022 in_progress and
023–026 pending. The prepared13-file future effort patch remains unapplied.

Historical start checkpoint follows.

### Continuation 2026-11-01: Remaining product checks

The distinct Chromium `/management` configuration workflow has started from
configuration `03349448`, retaining the original root tag and its confirmed Apply.
It uses the existing41 assertions and corrected driver `e9c9fbf6`; only the new
prefixed tag candidate may be applied. Its actual result must be inspected before
granting any conflict/recovery credit. Firefox multipart CSRF observation is being
prepared separately. The acceptance-scope proposal remains unapproved; required
coverage and task order are unchanged. A required repository Gate19 is being
prepared for the two test-driver corrections after Gate18; no runtime rebuild is
needed for those corrections.

### Checkpoint 2026-11-01: CLI/MCP reads and original-handle observation

[Rootless CLI/MCP3](../../../../.scratch/web-022-rootless-fixture4/rootless78-direct-cli-mcp3-result.json)
`c6bf5fb4` passes (0),20.594s: four CLI status reads and28 MCP calls across both
prefixes. Reports111/222 are synthetic; no genuine-worker or concurrency claim.
Attempts1/2 remain failed before any product request (wrong native credential path,
then umask-masked traversal); only existing stdin delivery/new test-directory0750
are corrected. [Native CLI/MCP1](../../../../.scratch/web-022-fresh-fixture2/native78-direct-cli-mcp1-result.json)
`423e1a85` passes (0),23.309s: the same4/28 reads through SDK78, joining genuine
Source75 full37523d22/revisiondf470523 reports exactly. No new job or concurrency
is claimed. Public detail is retained in each receipt's companion `.stdout`.

[Original-key import1](../../../../.scratch/web-022-rootless-fixture4/rootless78-original-key-import1-result.json)
`6812c64e` passes eight UI phases (0),40.794s: new manual LOCAL browser records for
original A-preview7762/A-Apply1dc/B-preview7e44 retain exact results before/after
reload; A's host outcome is confirmed/pending=false twice. Zero POSTs/errors, all
closures, configuration and three original results unchanged; browser39b80f6d closes0.
This never repeats Apply. Full13 conflict/recovery, old-B UI stale409, AUTH-05 and
normal85×18 remain open. Scope proposal remains unapproved; future23–26 patch is
unapplied, with high/medium/high/medium effort after22. WEB-022 stays **in_progress**.

[Direct retained-B API probe](../../../../.scratch/web-022-rootless-fixture4/rootless78-stale-B-api1-result.json)
`a03d6af5` passes (0),16.699s: exactly one POST `/config/applications`, with a new
privately fsynced key and original B's successful preview, returns409/HFAPI007;
new-key lookup404, no admitted operation/new API-worker-application records,
configuration change or pending state. This proves direct API refusal, not the
original-B UI stale-submit or full13 case. All started API/UI runs are closed;
no further testing/harness work starts while the user decision remains pending.

### Checkpoint 2026-10-31: Rootless78 tag propagation and SDK

[Tag2](../../../../.scratch/web-022-rootless-fixture4/rootless78-tag-propagation2-reuse-result.json)
`9af356bc` passes (0),304.114s: all six Chromium/Firefox/WebKit × root/management
cells and36 callbacks. GET/HEAD only; zero POSTs/operations, errors/console/CSP
empty, all contexts/browser/servers closed and all seven preservation proofs true.
The omitted Apply-filter action is corrected; original Tag1 `68828ce2` remains
failed. This reads the one original Apply's tag propagation without repeating it;
no full13 conflict/recovery, mapped-case or matrix acceptance is claimed.
[SDK78](../../../../.scratch/web-022-rootless-fixture4/rootless78-same-wheel-sdk1-result.json)
`0ee0aacf` also passes (0), with selected actors unchanged and tooling unselected.

Normal85×18 remains unproved: the modern stock-role lifecycle branch is absent
and `CASE_ASSERTIONS` maps only18 of85 case IDs. No harness implementation has
started. The [acceptance-scope proposal](../../../../.scratch/web-022-validation/web022-proportionate-acceptance-proposal.md)
is prepared and a user decision is pending; it is not approved.
Required acceptance and WEB-022 **in_progress** remain unchanged. WEB-023–026 are
pending; their bounded-testing/effort patch is prepared but unapplied until AFTER
WEB-022 and BEFORE WEB-023. User model data and its original HOME alias remain.

Record validation: `uv run --locked --extra server --extra mcp python scripts/check-docs.py`
passes (0),221 documents/29 helpers; `uv run --locked --extra server --extra mcp pytest tests/unit/test_web_plan.py`
passes (0),9 tests. These are bookkeeping checks, not installed acceptance.

### Checkpoint 2026-10-31: Rootless78 configuration observations

Rootless78 transfer, drain-stage2, switch, helper prepare/publish and application
start pass (0): receipts `b2761979`, `795039ed`, `b230ed21`, `ed17a724`, `1a91e1cf`
and `8531bae1`; [canonical read](../../../../.scratch/web-022-rootless-fixture4/rootless78-application-canonical-readonly1.json)
`4fe03f74` confirms installation. Drain-stage1 `1ff1248a` remains failed before
effects on an undeclared embedded-reader variable; the corrected stage is separate.
[SPA pilot1](../../../../.scratch/web-022-rootless-fixture4/rootless78-configuration-c03-pilot1-reuse-result.json)
`0cc1c253` and [pilot2](../../../../.scratch/web-022-rootless-fixture4/rootless78-configuration-c03-pilot2-reuse-result.json)
`96b25a6c` each pass30 callbacks, including28 normal/read/local-refusal callbacks,
then fail a preview locator wait. Configuration GETs return200, without the prior503;
only successful empty previews are submitted, with no Apply in either run.

[Pilot3](../../../../.scratch/web-022-rootless-fixture4/rootless78-configuration-c03-pilot3-reuse-result.json)
`00345d46` passes six callbacks, including two previews and ONE Apply
`1dc6b7fd053c10caa558f4cb7c3c32a9`, then fails an assertion equating opaque base and
candidate revisions. [Read-only qualification](../../../../.scratch/web-022-rootless-fixture4/rootless78-single-apply-readonly1.json)
`60a2fdce` confirms the original Apply, pending=false and only tagA changed;
configuration `03349448` retains28 disabled repositories. Never repeat that Apply.
The shared conflict actor alone now uses30s locator waits; navigation15s/callback45s/
helper deadlines stay unchanged. The assertion now checks `outcome.candidate_revision===A.candidate`;
driver `e9c9fbf6` changes two test lines after historical Gate18. All three raw
aggregates remain false; stale409 and completed13-callback acceptance remain unobserved.
The next prepared flow only reads tag propagation. Normal85×18 has not run: the
existing normal manifest is Source13, not78. WEB-022 and WEB-023–026 remain incomplete.
User model data remains preserved behind its original HOME alias at
`/var/tmp/web022-retained-hf-download-cache1/` (`8eb74eff`,274,049,435 B); no data is discarded.
No validation reruns or later-plan edits accompany this bookkeeping checkpoint.

### Checkpoint 2026-10-31: Gate18 and Source16/version78

[Gate18](../../../../.scratch/web-022-validation/gate18-result.json) 4417a816 and
[outer](../../../../.scratch/web-022-validation/gate18-shadow1-result.json) ec8c2133
pass (0): 9,645 backend, 4,051 combined frontend, 581 Cockpit and 16 wheel checks;
all 1,542 frozen files stay unchanged. Failed Gate16/17 evidence remains retained.
Clean Source16 `f829857ec045`/0.2.78 builds 19 indexed artifacts (0)
(`/var/tmp/w22b16/build16-postproof.json`,d8ac51b8); main stays0.2.2.
The first prebuild environment-clone failure remains separate from build success.
API78 image `1ece04ca` builds (0) (ef2268b3), foundation (0) (fd9dde04) and exports (0)
(5b418605); actual receipts remain under `/var/tmp/web022-api-source16-v78-build1/`,
`/var/tmp/api78-foundation-controller1/` and `/var/tmp/api78-export-controller1/`.
Input16 pack/render (0) has proof `a5583704` and TAR `ffb90eaa`/3,676,160 B/78 members
under `/var/tmp/web022-rootless-inputs16/`; this does not claim guest staging.
Native [A](../../../../.scratch/web-022-fresh-fixture2/native16-phaseA1-result.json) 1b77a6e2,
[B prepare](../../../../.scratch/web-022-fresh-fixture2/native16-phaseB1-prepare-result.json) 3c1ac141,
[B publish](../../../../.scratch/web-022-fresh-fixture2/native16-phaseB1-publish-result.json) 54c90ad7
and [C](../../../../.scratch/web-022-fresh-fixture2/native16-phaseC1-result.json) 0fba94fe
pass (0); C reports roles ready. Rootless78 upgrade and the existing 41-callback SPA
flow remain pending. WEB-022's 85×18 matrix remains incomplete; WEB-023–026 remain pending.

User-directed sequencing: AFTER WEB-022, BEFORE WEB-023 implementation, revise ALL
remaining plan-related documents for WEB-023–026 to keep testing product-focused:
reuse fixtures, bound machinery repairs and require concrete reasons for reruns.
Do not repeat accepted effects or reduce required acceptance. Record explicit
`gpt-6.1-sol` effort per task: WEB-023 high (compatibility/rollback), WEB-024 medium
(documentation walkthrough), WEB-025 high (retirement/safety), WEB-026 medium (evidence/
final gate/handoff), with scope/risk rationale and escalation criteria. Use low
for mechanical edits/commands; raise medium to high for a concrete contradiction
or diagnosis, with xhigh/max only for a named unresolved problem and demonstrated
benefit. [Testing directive](../../../../.scratch/web-022-validation/user-testing-guidance-after-web022.json)
and [effort review](../../../../.scratch/web-022-validation/user-model-effort-guidance-after-web022.json)
retain the instruction/source review. Later-plan edits are not performed now.
The following checkpoints retain their historical scope and pending statements.

### Checkpoint 2026-10-31: Gate15 and installed Doctor77

[Gate15](../../../../.scratch/web-022-validation/gate15-result.json) d6cef144 passes0:
9616 backend,4051 combined frontend,581 Cockpit,16 wheel and two built-browser
checks; all1541 frozen files remain unchanged. It is the latest full green gate.
Clean auxiliary Source15 `004ea9e270ef`/0.2.77 builds18 verified artifacts0
(`/var/tmp/w22b15/build15-postproof.json`,89f0649d); main stays0.2.2.
Native [A](../../../../.scratch/web-022-fresh-fixture2/native15-phaseA1-result.json)/[B](../../../../.scratch/web-022-fresh-fixture2/native15-phaseB1-publish-result.json)/[C](../../../../.scratch/web-022-fresh-fixture2/native15-phaseC1-result.json)
pass0. [Doctor2](../../../../.scratch/web-022-fresh-fixture2/native77-doctor-configured-port2-reuse-result.json)
a6117a8c passes browser/domain0 in ONE Chromium/root cell, original operation
`e82f4e1074fb0d6d35791442bcc67618`/run`c490d57b04de4e7ab038e51ec391d172`.
The configured25444 TLS/preflight fix is installed; old failures stay retained.

Native77 Library controls now pass all six browser/prefix cells: [root](../../../../.scratch/web-022-fresh-fixture2/native77-differential-technical9-root1-reuse-result.json)
0617de33 and [management](../../../../.scratch/web-022-fresh-fixture2/native77-differential-technical9-management1-reuse-result.json)
b1083782 pass transport/browser0 in129.973/127.986s. Each runs nine actual form
intents in Chromium, Firefox and WebKit: eligible GGUF/GPTQ, one-byte boundary,
same-variant conjunction and adapter/projector/unknown/incomplete exclusions.
All54 callbacks, strict health, closures and seven preservation proofs per run
pass; requests are GET/HEAD only. The same browser rootfs and installed roles are
reused with fresh browser contexts. These scoped observations do not replace
the required fresh canonical lifecycles or stamp a complete matrix case.

[API77 build2](../../../../.scratch/web-022-validation/api77-image-shadow2-result.json)
passes0: image`188ca49b…3fd6a6`, canonical record29f83635/result5334c8d7.
Rootless77 inputs pack/render passes0 (88533f46). Normal same-guest
[upgrade/start](../../../../.scratch/web-022-rootless-fixture4/rootless77-start-app1-result.json)
1594db34 now passes0 with actual983/caps0/NNP1/seccomp2/read-only roles, unchanged
configuration-only grants and original1790/NFS-ro. The unselected
[same-wheel SDK](../../../../.scratch/web-022-rootless-fixture4/rootless77-same-wheel-sdk1-result.json)
a0811c69 passes0: Python3.14.6 and119 hfcache package files join the indexed wheel;
selected actors stay unchanged.

[Read UI2](../../../../.scratch/web-022-rootless-fixture4/rootless77-readonly-ui2-reuse-result.json)
bbc0d139 remains aggregate1: five engine/prefix cells pass, Chromium/root fails
its host-permission text wait. The helper refusal reported a changed ancestor;
its exact cause remains unestablished, with no authority or hardening relaxation.
[Focused UI4](../../../../.scratch/web-022-rootless-fixture4/rootless77-readonly-ui4-reuse-result.json)
d2f9aeeb passes transport/browser0/all seven Chromium/root callbacks and ten
preservation proofs. Both runs close normally with zero POSTs/operations and
preserved archive/configuration/stores/keys/roles. Together they provide six
scoped read observations using the same browser rootfs across separate runs;
no fresh six-cell lifecycle or matrix pass is inferred. Original UI1/2/3 remain
false; UI3's preflight failed before browser/work creation.

Existing focused [Python checks](../../../../.scratch/web-022-validation/current-functional-existing-unit1-result.json)
373c9cd0 pass573 in the private read-only NAS shadow; [Node metadata checks](../../../../.scratch/web-022-validation/configuration-integration1-node-metadata-result.json)
e1db02c0 pass18. These source checks add no installed case credit. Gate15 remains
historical latest full green; current Gate16 and complete CONFIG03 remain pending.

[CONFIG03 pilot1](../../../../.scratch/web-022-rootless-fixture4/rootless77-configuration-c03-pilot1-reuse-result.json)
a492eefd remains transport/browser1. All28 ordinary configuration/read/local
refusal callbacks pass, with two pure validation POSTs200 and no operations or
Apply. The first conflict callback finds the test's new session still blank and
times out; a separate browser console reports implicit `/favicon.ico`404. All
three contexts/browser/server close; original stores, configuration, publications,
keys, roles and guard remain preserved. Correct session navigation and a local
indexed icon are being reviewed; neither failure is relabelled as a case pass.
The source shell now declares a133-byte local PNG icon; Vite captures it as an
indexed hashed asset under the rendered UI base. PNG already satisfies INV-019,
decision147 and the closed MIME/asset contract; no schema or CSP change is needed.
The existing browser-smoke server also serves PNG with its correct MIME type.
Actual build/prefix rendering and installed icon verification remain pending.

[Pilot2](../../../../.scratch/web-022-rootless-fixture4/rootless77-configuration-c03-pilot2-reuse-result.json)
76b0f8b4 remains1: the same28 callbacks pass, then sequential duplicate config
reads exceed the existing45s callback deadline. Two validation POSTs/no operations
leave configuration unchanged. The driver now uses the actual clicked response
and records prior28 evidence separately from the focused13 conflict callbacks.
[Pilot3](../../../../.scratch/web-022-rootless-fixture4/rootless77-configuration-c03-pilot3-reuse-result.json)
9c65568d remains1: concurrent session reads produce a genuine config GET503,
before any POST/operation. [Exact journal](../../../../.scratch/web-022-rootless-fixture4/rootless77-configuration-pilot3-helper-journal-readonly1.json)
56e2e9bc shows the peer observer deadline during fixed engine inspection, not an
observed ancestor mismatch. All contexts/browser/server close; original stores,
config393c2461, publications, roles, keys and guard remain exact. A single bound
configuration-read exchange is now implemented: the API passes only its immutable
archive UUID/root for comparison inside the same fresh helper read. INV-020 and
decision153 review preserves status/grant/profile/tuple ordering, legacy `{}`,
peer/configuration revalidation and every deadline. No further Apply is attempted.
[Focused regressions2](../../../../.scratch/web-022-validation/config-read-bound-authority1-unit2-result.json)
e6f9ae49 passes568/81.53s (outer85.218s) in the private read-only NAS shadow with
all16 source pins unchanged. Earlier regressions1 remains1 from temporary-path/
umask setup and five ApiProblem assertion errors; it is preserved. [Canonical wire
regeneration](../../../../.scratch/web-022-validation/config-read-bound-wire1-shadow-result.json)
81553c1c passes0/55 pins and both drift checks: only provenance digest changes;
public DTOs/routes/results and Unicode bytes remain exact. [Gate16](../../../../.scratch/web-022-validation/gate16-result.json)
cdd6da6d fails documentation alignment before tests/build, with all1542 inputs
unchanged; formatting/lint/types/wire pass. Its ADR143 execution-record link and
work-package identifier are replaced by a living development-contract link and
general staged/final matrix wording. [Gate17](../../../../.scratch/web-022-validation/gate17-result.json)
7df71e7d remains1 after9645 backend passes, three locked wheel profiles and581
Cockpit passes. Web lint rejects a cleanup throw inside the test driver's finally;
the minimal correction defers that throw until after finally while retaining the
original error. Full web ESLint/Prettier now passes. All1542 inputs stayed unchanged
during Gate17; no product runtime code changed for this correction. Full Gate18,
new Source16/version78 artifacts and the existing41-check SPA flow remain pending.

Completed Source12 generated dependencies and successful573-test TMP retirement
passes0 ([retained result](../../../../.scratch/web-022-validation/source12-generated-and-successful-unit-retirement1-result.json),
f1f53abf):585,900,032 B gained, root2,575,294,464 B. Complete inventories/package
metadata remain under `/var/tmp/web022-source12-generated-and-unit1-retirement1`;
original source/all18 artifacts/logs/current dependencies and unknowns are preserved.
Eight exact completed API76/77 builder-cache images then retire through normal
`rmi --no-prune` (a72c09b7, `/var/tmp/web022-api76-77-builder-cache-retirement1/result.json`):
387,756,032 B gained; both finals/foundations, other layers, donors and OCIs remain
exact. Normal cache-only DNF cleanup passes0 ([result](../../../../.scratch/web-022-validation/system-dnf-cache-clean1-result.json),
02ccca74), gaining53,604,352 B without package installation/update. Root free reaches
3,016,597,504 B; future API builds must recheck the unchanged3 GB start floor.
Qualified unit/gate TMP and generated-dependency retirements pass0
(29fe4b24/57b8605b/c98a7981/07a6d287). Twelve evidence trees and the headless
runtime retain complete copies/original aliases (d99a8382/49e60bc5), gaining
29,270,016/286,101,504 B HOME; no VM/archive cleanup. The3 GB build floor stays.

The split-guest execution contract preserves real paired lifecycles,
artifact/role authority and85×18/95×18 requirements; it is not acceptance evidence.
New test/record changes require a later full gate. WEB-022 remains open,
WEB-023–026 pending; prior observations and failed aggregates are not relabelled.

### Checkpoint 2026-10-31: observer completion, repair and capacity

Historical snapshot before Gate15/installed Doctor77; pending statements below remain historical.

Observer C [qualification2](../../../../.scratch/web-022-fresh-fixture2/native76-fresh-observer-release1-effects-qualification2-result.json)
d08b35d9 passes exit0/all11 proofs; raw C remains1. [Completion UI](../../../../.scratch/web-022-fresh-fixture2/native76-observer-backend-completion-ui1-reuse-result.json)
42e758a2 passes four callbacks,29 rows, same-original reload/zero POSTs and seven proofs.
[Repair3](../../../../.scratch/web-022-fresh-fixture2/native76-finding-repair3-reuse-result.json)
68b2e41a passes13 steps/eight proofs in ONE Chromium/root cell. Original Repair1/2
remain false; seven POSTs/six original operations prove Verify exit40 → Repair exit0,
new21770… generation1 → Verify exit0/two files4751B, old-bookmark no-fallback,
current integrity and reload. Health/closures pass; full case/matrix remains open.

Gate9 generated-TMP retirement0 (`/var/tmp/web022-gate9-temp-retirement2/result.json`,
25b0ae79) gains 925,540,352 B; root free 2,426,048,512 B. Eight builder-cache removals0
(`/var/tmp/web022-eight-old-api-builder-images-retirement3/result.json`,1c3bfaf7)
use normal `rmi --no-prune`, gain 391,405,568 B; root free 2,817,437,696 B. Other records,
API76/foundations/donors/OCIs/proofs remain. Combined net gain is 1,316,945,920 B;
the 3 GB floor was then unmet. Old public74/75 foundation retirement2 also passes0
(`/var/tmp/web022-old-api74-75-foundation-retention2/result.json`,00f5d8ca), gaining
292,487,168 B/root3,106,091,008 B after four normal engine actions. Original CID/MCS/
spec metadata and57 public file copies, OCIs/proofs remain; current76 is protected.
No VM/archive fixtures change; future builds must recheck the unchanged3 GB floor.

[Manual2](../../../../.scratch/web-022-fresh-fixture2/native76-ordinary-manual-jobs2-reuse-result.json)
a389929c passes UI/recovery, closures and seven root proofs. Combined three POSTs/
three original operations plus one estimate show Refresh0/warnings and NEW0,
zero scope/`clean`; raw Manual1/5cdab3e4 remains false on the private `clean_empty`
expectation. Doctor domain fails20/HFHUB002: configured port25444 but preflight443.
Its15 checks show four probes pass, TLS fails, identity skips; the UI correctly
renders failure. The source port fix is implemented; [targeted green checks](../../../../.scratch/web-022-validation/doctor-port-green1-shadow-result.json)
53a678b3 pass224/2.81s after the retained red failure. Gate14 fails at the source
wire audit before tests/build (inner3c78fcba/outerde30bb68); all1541 frozen inputs
stay unchanged during that attempt. [Canonical wire regeneration2](../../../../.scratch/web-022-validation/doctor-port-wire-regenerate2-shadow-result.json)
passes0/84ebded7 (inner17225bd8),
all55 pins/two drift checks0; only IR source digest/two TS digest occurrences change.
DTO/route semantics stay exact. Required gate15, rebuilt artifacts and installed
Doctor acceptance remain pending. Historical gate13 is the latest full green gate;
WEB-022's85×18 matrix stays open, WEB-023–026 pending.

### Checkpoint 2026-10-31: maintenance, authentication and source validation

Historical snapshot before observer C qualification and repair; its pending statements stay historical.

[M10 qualification2](../../../../.scratch/web-022-fresh-fixture2/native76-owned-maintenance10-effects-qualification2-result.json)
5e5b7ee4 passes0/all11 proofs/finite12 cache paths. Original parent e17f2343
stays1 on normal Purge cache removal; browser0/6b1c75b4 passes all six steps,
5POSTs/4successful operations, removal-without-purge and only-new903-copy Purge.
Qualification1/a2f482e remains1 on the final read-only ArchiveLayout(str) collector
call;2 changes it to Path, without replay. Old ten publications/reports remain.

Authentication branch ends partial: Chromium’s original2+6 Origin refusals remain
scoped. FF/WK5/605503f1 stays1: Firefox text401 bodies unqualified; WebKit six
nonopaque cases pass but null403 capture adds source-automation CSP errors.
FF6/22e4991e stays1 on form401/body-unqualified observations. [FF7](../../../../.scratch/web-022-rootless-fixture4/rootless76-auth-cross-origin-firefox7-reuse-result.json)
47d8bba9 observes all four final attempts: two opaque null-Origin403/HFAPI010 pass;
two multipart cases are limited by401/challenge metadata versus104B
HFAPI010/Forbidden/exit10 bodies. No qualified auth401 or inferred older bodies/app
bug follows. All close/no operations/preservation passes except scope; full AUTH-05 remains open.

Observer A31260f15/activation9c296abb pass; old SDK stays failed/retained and
new state is separate. First root review543ef272 fails an overstrict old-SDK
assumption;36fd1b6e corrects it. B browser Stop succeeds/confirmed/pendingfalse,
SDK exits20; raw parent0a6dd3d4 fails a shadowed-unit lookup, [B qualification](../../../../.scratch/web-022-fresh-fixture2/native76-fresh-observer-ui1-effects-qualification1-result.json)
e9a78770 passes0. After one explicit reviewed signal, holder exits0 and original
backend succeeds:29rows/28disabled/1skipped, zero totals/HFWRN011, current9 generation3
and old ten unchanged. C parentfc66c3b5 stays1 on a post-pidfd zombie assertion;
read-only qualification is pending, no release replay.

Native pre-A metadata capture8087c178 passes0 without lifecycle/case credit.
Rootless capture094318f4 fails before WORK on inherited-cwd permission;2 changes
cwd only and is prepared. Role23 unit checks pass; tracked F8/tag/config/referrer
updates still lack a fresh full gate beyond gate13.85×18 remains incomplete;
WEB-023–026 stay pending. This checkpoint precedes C qualification.

### Earlier checkpoint before maintenance closure

Rootless negative configuration coverage is explicit five-plus-one, preserving
its failed aggregate. Native nine technical queries pass one cell; rootless18
technical checks remain partial. Tracked tests add F8/six variants, Tag19,
ordinary drafts/24 local refusals and the valid-POST referrer policy. Role drift
[checks](../../../../.scratch/web-022-validation/installed-role-unit-shadow4-result.json)
pass23; no full gate follows historical gate13, and lifecycle mappings remain open.

[M7](../../../../.scratch/web-022-fresh-fixture2/native76-owned-maintenance7-reuse-result.json)
records9POSTs/7successful operations through EApply/firstSync, retention3Apply and
Prune, then a JSON-expander assertion fails. M8f82ca6fe refuses before browser;
GET-only reuse2/5e3c6a86 observes seven originals/currentE/retention3, then misses
a collapsed disclosure. [M9](../../../../.scratch/web-022-fresh-fixture2/native76-owned-maintenance9-reuse-result.json)
5a1f7be9 passes Prune publication/transaction, displays oldB unavailable/no-fallback,
then waits for the wrong Overview tab; that step remains incomplete. M10 at231.8s
passes three steps including explicit currentE; original Sizing/RemoveApply succeed.
Confirmation/reload continues; Purge and the final result remain unobserved.

Auth1/2465c78e remains false with44 browser denials; Node protocol2/cb1644c6
passes ten403 checks. Leaf source3/4075b6b2 refuses before effects with16.6h CA
remaining. Source4/54400109 signs once but verification at a prior time fails;
[existing-leaf qualification](../../../../.scratch/web-022-rootless-fixture4/rootless76-auth-cross-origin-source4-qualification1-result.json)
a0ebd243 passes without reissue (18:43:04–20:43:00UTC). Browser3/2aae20e3
records two real source-Origin text/plain403/HFAPI010 denials, one per alias;
Authorization attribution is unobserved, not authenticated-CSRF acceptance.
[Browser4](../../../../.scratch/web-022-rootless-fixture4/rootless76-auth-cross-origin4-reuse-result.json)
a905ca44 passes six fresh form/multipart/opaque denials (four source-Origin,
two true null-Origin), all403/HFAPI010: explicit2+6=8 refusals. All native
clicks, strict health, nine root proofs, closures/listener/socket drains pass;
no operations/effects. Authorization remains unobserved for all eight; original3
stays false and full AUTH-05 remains open.

Same-host `/var/tmp` TAR5/74028e30 preserves HOME257925120→293117952B;
TAR6/48e3f025 preserves279613440→533913600B, ROOT1758830592→1493221376B.
Original aliases/bytes/metadata remain verified; no VM/image/unknown cleanup.
85×18/WEB-022 remains incomplete; WEB-023–026 stay pending. Cheap checks await M10’s actual result.

2026-10-31 actual continuation: native focused configuration follow-up passes
transport0/browser0 in23.335845s, case10.439921s, in
`.scratch/web-022-fresh-fixture2/native75-configuration-read-followup1-reuse-result.json`
SHA25687aad72192e4ccb5714a5b0abb5db0511fc0d5959763e13e2fd4810b6b6509b1.
HTTP200 plus exact base/draft/action assertions and all five preservation proofs
pass; normal context/browser/server closure holds. The raw passive request row
retains an ERR_ABORTED close observation after its200 response; this is not
relabelled as a completed transfer. Old native-six aggregate remains false.
Cheap record check5 passes docs221/29,9 plan tests and outer0; receipt
69184ba224dc2e44b53b56c127af5368197b0353e0f961b8496fce51a847026b
and shadow0596167e2a248b4e8b9003c9feb8b3967e882339cc48c74c48782748fb1f3533
cover the preceding unchanged four-record snapshot, not this update.

Public differential input generation0 produces29821B across three revisions,
8files/16926B for the present revision; generatorcf86b621… and finite check-only
receipt7a65c192… prove origin bytes only. Actual owned Hub setup passes0 in4.052s,
`native75-differential-hub-setup1-result.json` SHA256
bc8c26fd8d7d08c3840b7f83caaa4af3e096a2afb7e3703f382f850b581bed07:
new listener70923/start6454630/invocationeb516342d7454fc2bebf16c036c24275.
Old56271 exits normally0, final counter/source/13inputs/cert/key inodes remain;
all API/helper/worker/Caddy roles, archives/stores/config/browser/key/CA stay exact.
The successor adds only finite owned7/8/9 views and masks both actual backing
parents, retaining nobody/caps0/NNP/seccomp/loopback-only hardening. The prepared
mutating manager wrapper's deadline is removed before execution, with original
prepared files retained; no actual manager action is force-terminated.

The first present UI invocation exits1 at host launcher line21 capacity assertion,
before its exclusive intent, SSH, browser or any POST. Home84574208B is below the
unchanged268435456B reuse reserve; root2257170432B is available. Exact host-only
refusal `/var/tmp/web022-differential-present1-capacity-refusal1.json` SHA256
10f234d0be659b6d3a6335ba601d4eb88a5bfa699d08f2710c9671ad8a65b7ec is
retained with no effects. Subsequent eight-output static preservation completes0,
`/var/tmp/web022-retained-static-packages2/result.json` SHA256
45758383b101460585b4ab0821947a840a6973bb710449b77e3e082e5887a817:
Home76840960→516915200B/root2254680064→1815547904B. All eight byte/semantic-metadata
copies and old-path aliases verify; only exact duplicates retire. Artifacts stay
on this host's `cs-root` under `/var/tmp`, separate from `cs-home`; no guest change.
Cheap check6 result SHA2561c3fd0e24e9d5712a2a7b6c8dff6bc34e91aa384228c0782c6cd42679f91cd13
passes docs221/29 and9 plan tests; shadow0, prior snapshot only.

Installed pure plan0, `/var/tmp/web022-differential-present1-pure-plan-readonly1.json`
SHA2568328540137268db2d2664b3d2ac98037db705b48e565313e9da5d6ccfa5c6824,
confirms max-retention3/28 disabled/903a88 age58.9327h against24h and exactly one
quarantine-staging action, blocked0/problems0; no job/lock/write/reconcile occurs.
The parent corrects semantic default parsing before execution. Present1 then
fails on observation of a valid retained HF-cache symlink, result SHA256
26d7f7b26bc793ce2a16e84f1ed62beb05e66ce1a12a23470f038bf8ab0d441a.
Readonly qualification SHA256
0d4979150b0a7f7f355fbcfb97872bfb091f40272af2ae3e30952cda66822a17
proves no new WORK/output, config393c2461/smoke34f/CIDclosed0/a88 unchanged;
numbered2 permits only symlink lstat metadata/target without dereferencing.

Present2 actually remains transport1/browser1 in106.141s,
`native75-differential-present2-reuse-result.json` SHA256
8a3cf850623db55d80575329c51aa896c31943258c07599e13b9d4fac6a51d29.
First two UI steps pass. Original Sizing2e0008c93aca45413def805515db43f9/run
2190b04e6a7d46bf84b39d9686327007 succeeds; original Apply
5b4bef0012d2ef53fb296b08739e138b/run878d8d140ebb4d39b3c51c4290cee7a9 is
confirmed/pendingfalse. Parent joins original key/backup/predecessor and proves
normal Apply adds only the enabled7-SHA differential model to28 unchanged disabled
entries, retaining every old field. Browser then fails a late Edit-button lookup
because the new entry is on page2 of the25-row list; this is a test pagination
error. No Sync/admission POST occurs. All seven old publications/unknown siblings,
old real archives/private originals and app roles/original1722 remain exact;
context/browser/server close, with zero page/console/violation/5xx errors.
Present3 remains transport/browser1 in12.524s, result SHA256
2cf6a7c404da7b612ded9948a1f5651cd7e8b9e3ac300fa9560e284ec7d308ff:
its first sizing GET recovery compares a dynamic HTTP request_id. Present4 remains1
in56.636s, result SHA256
6fb6e5aa1d8db756e0621bdf8d3277519933eecc1df195373d574fce0ce95f34.
Restoration/UI Observe of BOTH original Sizing and Apply plus host confirmation
pass, and page2's actual Edit button is enabled; the next tags assertion fails
because its nested filter searches for a configuration-region scope inside an
entry. This is a test locator error. Both runs send zero POSTs/create no operations,
close all contexts/browser/server, preserve the four other root proofs and report
zero errors/effects. Original Apply and a88 remain unchanged; no Sync occurs.
Present5 is terminal transport1 in82.176s, parent stdout empty, result SHA256
c95ebc5f5664b63b7ed5e44e88b4a4b1e86b8246847fa34f295669076ac8e2ac.
Readonly observation SHA256
4de9e729fd90e00cdb4aba3d2780474ab21316be656d1d9fad57f1d6137f9e1a
retains actual browser REPORT1: first five steps pass SAME-original Sizing/Apply
observations/page2, one FIRST selected Sync, same-original reload and loaded
hostile README64-row table/3 code blocks/4 encoded URLs blocked/generated IDs/
exact sanitized source. Step6 Files fails on `.status()` of a null Response from
normal same-document hash navigation; Files/variants/nine AND queries are unrun.
Exactly one Syncdfb7fc973dd4f4728f0a6d163fb9d1d1/run
653ebff503d24f55bbc27cf037f7b119 succeeds0,7-SHA publication
e6ad4b8a45ae4090a7446e552cf926f3/generation1:8files/16926B downloaded/published,
reused0. `completed_with_warnings`/`success_with_warnings`/HFWRN011 are truthful,
not replaced by an unqualified clean status. Normal first-Sync TX-07 quarantines
known a88 and closes it failed/HFTXN003; Recovery run
14db4cb98623480bb96ed571a4817041 at
`runs/20261031T105946Z-14db4cb98623480bb96ed571a4817041.json` records one applied
quarantine remedy. New Sync0cbbae4f5cea4f1b81ab5efc27f98026/publication
3d648f60b27a4317898ccb0f3e0fa337/recoveryd3af1bb06de94490a153a1d6282a8857
journals commit. Parent then fails its collector assertion on nonexistent top-
level publication_id; the actual ID is in revision_ref_published checkpoint evidence.
Read-only qualification1 remains failed in2.672s, SHA256
4aa7617fd7a5e3d5a07b691b854bcebe337f6457adfcbae73124d152e9f3ecaf,
on one new normal HF-client `CACHEDIR.TAG`. Root's read-only observation proves
it is the only extra191B file, UID/GID983/mode0640/nlink1, SHA256
f6572428f6d5e1575e73a1502895a8731f10757dfbb634909c6e154b849af91d,
byte-exact installed Hub constant. Before execution, a prepared collector's
shadowed `before` variable is corrected to `original_before`; prepared originals
remain. Qualification2 then passes0 in3.321s, SHA256
2539ceedaee94b2e8ff92da0f1aa269dac6eac0d19e221b04b06ee1119d99f4f.
It permits only that marker plus exact reviewed new-repository/recovery effects,
finishes all old seven sets/unknown siblings/old real archives/stores/keys/browser/
Apply-Sizing config29/history preservation and actual dfb7 Sync/e6ad publication/
14db recovery journal/report joins. Current files remain unchanged during these
reads. This qualifies effects/preservation only: original parent/browser/Files/
variant/filter flags remain false, with no replay or whole-UI acceptance.

Generated adjunct read0 independently confirms six variants: primary GGUF1184B/
bits4/Q4_0, primary GPTQ84B/bits8 with source config, adapter1216B/projector1216B/
unknown1184B/incomplete1248B with incomplete bits unobserved; coverage is partial.
Actual card is present,10631 sanitized bytes, source81cfe601…/presentation069f…;
these API/adjunct reads alone supply no remaining UI credit. Root copies and
visually reviews `actual-original-Sync-after-reload.png`,694205B/SHA256
198abc4ef262e7e183fcbd9e6a081f67898e35c84049ef4bbfb13af002252733,
and rendered README628578B/SHA256
520bee6b871ba8a369ce5a5f376aea4da514062d07d938c30e8620da18a35509:
actual warning/16926B counters and64-row table/inert fences/partial coverage.
Pure-GET present6 remains transport/browser1 in61.843805s, result SHA256
64336af77dd9e566e4bcdf7f8d919b178e722c8821829c05917f974214c1b64c.
First four steps pass, including exact eight Files/six variant roles, then four
AND queries pass before the fifth encounters CDP response-body timing failure;
no app defect or mutation is observed. Fresh pure-GET present7 passes transport0/
browser0 in86.001619s, `native75-differential-present7-reuse-result.json` SHA256
7377d112000162d3d23e6e145db9861217d6f31a6cb2cb347a0465b16e472314.
All five fresh steps and nine differential queries pass: SAME-original Sync GET/
visible truthful warning counters, current29 protected config/old seven sets,
loaded hostile README/source/links/headings, eight exact Files/six roles and
same-variant AND/byte-boundary eligibility. Zero POSTs/operations, all context/
browser/server closures and all six root proofs pass. This is one Chromium/root
cell using the same browser/container/rootfs, with no copied present5/6 pass or
mapped/full85×18 stamp; all original failures stay. No Sync/Sizing/Apply repeats.
Native29 configured/30 union/8 retained supersedes old native28/29/7 carriers;
rootless remains its independent28/29/7 fixture. All preservation stays on the
same host's root `cs-root` under `/var/tmp`, original `cs-home` paths are symlinks.
Fresh free after7 is root1815605248B/home470507520B; prior relocation before/after
values remain historical. Gate12 now passes current3855/freeze4 inner/outer0
in1929.297492/1929.998999s, all1006 frozen product files unchanged. Inner receipt
SHA256e82ebf1772f551659ddbc090ca62fec9ddb9e3582a9a2a7ba3c6cd2c9716e97d,
log48cd1cc640aadf935a88e94b7ffed16f0a576284018e4771e14e8217fd708339;
outer5e696df8c2917c0730a1d9e0556e72e7b5fe0015b85f184d88fd459741baf7c3.
Backend9580/52 opt-in deselected/1431.21s, web unit3708/combined4049,
95.02% line/90.16% branch coverage, Cockpit, two built-browser startup/real HTTP
reads, three locked wheel profiles and16 wheel smoke tests all pass. Full85×18/
CARD gaps/WEB-023–026 and old unknowns outside903 remain open/protected.

Revision8 attempt1 remains transport/browser1 in52.083538s,
`native75-differential-unsupported1-reuse-result.json` SHA256
792c05bafcf2de9aa5546e1eac7424cabf452fd0a9da2eb638cf13b27e5b91dd.
Its three old-original Observe checks pass, then a10s exact draft-base wait fails
after config HTTP200. Attempt2 remains1 in68.518704s,
`native75-differential-unsupported2-reuse-result.json` SHA256
83d7fd4eb1bb72dc4479e05f3417844b3e98afdfeb9e3e094717ffcd1a1d6ef4:
its exact post-click completed-response observer reaches35s. Actual failure DOM
`native75-differential-unsupported2-actual-failure-ui.json` SHA256
c8144aacb9b83fb37c97f74ffd176bce940978886dc097ceefad4df72e030888
and root-viewed PNG93987de3… show the editor loaded exact base38cc00c9…,
29 rows/a clean draft/no alerts. Pre-click GET16 completes/captures its body in
13.967s; clicked GET21 receives200 in10.178s and ERR_ABORTED at10.254s.
`web/src/api/client.ts` finally unconditionally aborts its controller, including
after successful strict decode/return. A CDP completion observer cannot gate UI
success; this proves neither a failed UI read nor a completed clicked transfer.
Both attempts send zero POSTs/create no operations, close all browser actors and
retain old state exactly; no app defect is established. At those checkpoints
native stays revision7/29 configured/30 union/8 retained without publication8.

Attempt3's original parent remains transport1 in242.713405s, result SHA256
ac90e46f4ce9c6002cb79868872c138c074a981ff46bfab3d19310c901840f2e,
stdout empty on its old cache-lock timestamp expectation. Independent actual
read-only effects receipt SHA256
c2c6a2a058747046c62d9dfbd0ea26d6711a73a0eb1356265fb3608bbfc0aa80
retains browser PASS/all six steps/closures/zero errors. Original Sizing
be9f67668ca242fab917340e46f5d26c/rund537944d693049eea36f0de45ec06053,
Applye163b5be770843941581bf1e7343b0e2/runf5e6b63d487c40e190dbd17d7878cdd0,
and Sync7ff01405e9da7ed29524569fc6138eb7/run45293c446be942a1a924034e0a1062ed
succeed;8-SHA/5ef704ee0e3341f9abf4edb5ff7b9df1/generation2 publishes6609B,
downloads382B/reuses6227B with truthful HFWRN011. Retained7 README/source and
current8 unsupported/body-withheld/no-fallback all pass in one Chromium/root cell.
Root-viewed current8 imageaf23b418… and retained7 imagedadfe607… cover their loaded
README states; other metadata panels still Loading give no completed-panel proof.
Qualification1 stays1/5.155s/395974b9… on a wrong vendor-helper assumption;
qualification2 stays1/6.792s/ef671e24… on omitting normal revision8 tree JSON.
Actual tree receipt12a67a41… joins exact8 origin sizes/Git OIDs to its863B cache
inventory/SHA256ff46819f2d0ce66bed567a45f764a54f1688e6915b41f5ee78b3d2c0c2f6716e.
Read-only qualification3 passes0 in9.593849s,
`native75-differential-unsupported3-effects-qualification3-result.json` SHA256
9ca547c1a297b12314d1a5ce66c3ef7c90001241f3eacb5ca5da48c8190dc82e:
qualified/original_browser true, original_parent false, all seven boolean proofs
true. Only14 actual shared-payload nlink+1/ctime rows and seven manifest-bound
empty cache-lock mtime/ctime changes are allowed; other old/current state stays
exact and unchanged during qualification, without new operations/browser/actions.
Native reaches29 configured/30 union/9 retained/current8 at this checkpoint;
all original parent/qualification failures remain false.

Actual revision9 passes transport0/browser0/all six UI STEPS in ONE Chromium/root
cell in237.506228s, `native75-differential-unsafe1-reuse-result.json` SHA256
8a34e9c175111492f619720591bf47297433f4dd8420a24c2766569f1a17d24c.
Original Sizing0025e3ba9e7d0df4628d9ff1f2e29485/run
18e639bbc28845d6b6a087de4ae016af, Applyceb630cd1565f6f0e0ebfc8ffb83e04f/run
0f4bb6fb1d984bffb176514e607dbc25 and Syncb7c99ad47b9144b346921f4bc99d3c6b/run
7d59c099f8434b7f8b592e2af5a6a270 succeed. Publication
ed17f321a0474ee6996107190c73807f/generation3 publishes6286B, downloads59B and
reuses6227B with truthful HFWRN011, without a new Recovery. Current9's unsafe/NUL
README body is withheld/presentation null; retained8 unsupported, retained7
present/source and explicit-current9 no-fallback UI all pass. All contexts/
browser/server close, errors stay zero and all six boolean root proofs pass;
only21 shared-payload link/ctime rows and seven manifest-bound empty cache-lock
timestamps change. Native now29 configured/30 union/10 retained/current9;
independent rootless stays28/29/7, old unknowns remain protected.
Actual six engine/prefix read aggregate remains transport/browser1 in423.232197s,
receipt SHA256a44f42d9fbbfa9887f539c5355d7e21f4b578096cc30fd9a25936374d4196bce.
Chromium/Firefox at both aliases pass all six UI steps each. Both WebKit aliases
pass authority and every loaded README DOM/source assertion, then two screenshot-
related CSP console errors fail strict health checks; the failure image adds a
third. All contexts/browser/server close, zero effects/three root preservation
proofs hold; aggregate remains false and its final probe is unrun.
The separate actual search/type probe1 remains1 in21.769995s, receipt SHA256
21598052ca33bf2cf95ed7658e98ee74a06b3476fb322f603636445379759734:
actual fill→Models75.2ms clears typed q/field/hash, yielding HTTP200/15 models
instead of the expected1. Closures/no effects/errors0 prove a genuine UI bug.
Contract-first correction changes only `docs/web-ui/library.md`,
`web/src/components/Library.tsx` and `web/test/library.component.test.tsx`:
current DOM q is applied with type through existing validation. Two literal-
Unicode/pending-clear regressions fail before the fix;23/23 component tests,
lint and format pass after. Fix receipt SHA256
5c84e988185d2387999a20196b7dd08bead4f9afff2cdd11eeb9767f5173e4fc records
INV018/021/ADR145 review, no new architecture/dependencies/CSP change. Required
post-fix gate13 and clean installed UI-artifact regression remain pending.
Independent screenshot diagnostic0/browser0 in20.711879s, receipt SHA256
6f6094d6a9b1991cddd3608302f4520870f5f4dd8c3387e439618687bd36136e,
loads actual README/exact source with console0/CSP0 before capture. One Playwright
screenshot injects transient HEAD `body {}` and produces inline style-src-elem/
console refusal at the same instant. All root proofs pass; this is test-actor
behavior, with no product CSP weakening. Fresh strict no-screenshot WebKit
follow-up passes transport0/browser0 in244.487418s, receipt SHA256
818d8c17b9e15fb1e90372f6cfd7eff604545ef65adade484ada62ec9298f4ee:
both aliases pass all six steps/nine AND queries each, console0/zero effects,
all closures and all six root preservation proofs. The nine-query aggregate
steps take46135.314/77523.793ms within the existing120s pilot scope; strict driver
45s remains unchanged, without performance/mapped acceptance. Combined with the
four earlier Chromium/Firefox cells, these are six source75 native read cells;
original a44f aggregate stays false and supplies no copied whole-run pass.
Exact gate12 generated TMPDIR alone retires0, receipt3a91b6d7…:179508 entries/two
privileged no-reference checks, root882089984→1807298560B, logs/results/source/
inventory retained. Gate12 stays historical pre-fix green. Required post-fix
gate13 now passes inner0 in1849.131650s/outer0 in1850.052418s, all1006 frozen
files unchanged. Inner receipt SHA256
dca41acd2b59efb39287c92dc78abe2d645fba2fb7ea73e21b762219046537b6;
outer0a0c45c82dd7e03720397cccc8cb9450ed580a3b6acbd653aa06ae1f326e8736.
Backend9580/52 opt-in deselected/1358.64s, web unit3708/combined4051,
95.02% lines/90.13% branches, Cockpit/16 wheel smoke50.07s/two built-browser/
real HTTP/three locked build profiles pass. Source14 clean cut0 has commit
d4d99f8dde2b7bbc9b954da59f33bf8ec483967d/treeb0352c3b69117025a4778e97ffaca9dd3292cbd3,
receipt55323244f05ad5f19089dbb3e1007725b34ea7ef272f2970f10e9724aafbf778.
Its seven frozen changes versus source13 plus two fixture-version76 inputs leave
main0.2.2/refs/index/all1006 unchanged. Native14 build passes0 in15.233s,
`/var/tmp/w22b14/build14-exit.json` SHA256
b4eaf3aee07cc6c377894c91bec9fda91ad2929a27711f29843e33078fc8669e;
postproof620873aaeba31f9b2660721587fd08f2e376aa8684d5dae4c3d7db0f1b98c2ae
and shadow18bf671b… pass:18 artifacts, clean source/reproducible backend/UI,
indexe03e8b43…/UIba76372c…/source3c59e387…, main unchanged. API76 canonical build
passes0/98aae0b45f587101f5f1c182d194b0f006e8744ca0ef8dff9e88c4dca87a43d4,
with old images/catalogs/contexts/product preserved. Canonical API76 runtime
foundation now passes0 in14.083s: e529c2ebfad64e3ea4af1babf9c4768163fe778f28cf5fb7fa57be63c38f3a63,
proof93c873f6cc7b77aaffcdb9628bd18a944156848fd2120c9145c442b767b730c4;
private-shadowb4bfd789… exits0. No reserve/store/main changes or guest/installed-
qfix acceptance follows from foundation alone. Native76 now installs by normal
A/B/C0: A e1b11a1c…/109.649s, B preparedc726678…/publish451293b7…/review677845f5…,
C8228400df2a1ed8eb54f5e76b0c6169c23d84e3b688f2d932cbe09eda4f84fe2/20.718s.
Original1722/keys/archive903/stores/new full37523/revisiondf470/Hub stay retained;
19 bindings/six grants and original SELinux receiptfe124… remain unchanged.
Normal new helper86976/worker86996/API87017/Caddy87027 run76 with owned NFS-rw.
Installed q6 aggregate remains transport/browser1/99.21s, receipt SHA256
71235451b43d7fdbdeef2496864abc5bdb68e8f2ff3a54c207446c7aeacc52a1:
five cells/ten literal+clear cases pass, while WebKit-management's406ms typed
click is timing-unobserved and clear is unrun. All closures/health/preservation
hold; no new app bug is inferred. Fresh exact WebKit-management2 passes0 in
27.528s, receipt SHA256
6f35217acb9433dd7d1f97810078f0860a7182b2e933afec5343a0a07314340c:
actual85/84ms clicks,3747/3969ms observations, both cases/strict health/closures/
all seven root proofs pass. Together these prove installed76 q-fix coverage in
six native cells without relabelling the original aggregate or source75 failure.
Rootless input14 pack0/6d4d188c… after build/foundation/export0 now leads to normal
rootless76 app start0/bda51883… and actual q/type six-cell0 in97.165309s, receipt
19d7e7c31ba7c6d01bad0c064e6777eb5abfb5d6020059d5cf0e22688de0fb97.
All12 fresh cases/strict health/closures/six root proofs pass, zero operations or
effects; rootless28/29/7 remains separate from native29/30/10.
Native first schedule remains failed530db125…: validation200 and exactly one
replacement202 precede ec6747dc582ba18ec65420e5ed82fca0 interrupted/resultnull.
Authenticated foreign3f history rejects before PENDING/host effects. GET observer
830efb44… remains aggregate1 solely for the expected direct409 console diagnostic;
offline scope184ac01a… qualifies actual original-key UI lookup/Observe200,
unknown/pendingfalse guidance, blocked submission, retained key, all closures and
preservation. This does not reconcile, replay, or relabel the original.
Same-guest fresh control prepare0/eee774bc… and independent review3627a890… retain
old `/var/lib/hfcache/api` untouched at its path and the foreign history/empty
backups/server inode in private `fresh-control1`, with903 payloads/reports/worker/
SDK originals/keys/locks exact. Only supported server.state_directory changes to
`/var/lib/hfcache/api-web022-native76-control1`; neutral65e929fe… remains byte-
identical with no authority writes. First restart7ec644f8… stays failed after
four successful normal starts, before observing the store lock. Later read8255fa8f…
finds exact empty `.lock` inode54280926 held by API89764/fd16; a startup-readiness
race is consistent, not established as the cause. Read-only qualification2 passes0
in5.279256s, receipt SHA256
a72d807a9ba1449c9c619861852918c726af6e6741080dafe845734e6a44478a,
joining the SAME four started roles and all preserved state with zero new starts.
It creates the truthful qualified protected activation result; original7ec stays
false/ec674 unresolved. Schedule summary0 now records scoped six-cell behavior,
`native76-schedule-six-cells-scope1.json` SHA256
cd798799a3e19a4ce86e3ade3958d05038a12e438b5c13ec99d4c254792d9aac:
five full sessions plus Firefox-management's explicit2+2 continuation,24 unique
confirmed keys/operations and all six final default/inactive. Raw Firefox9dae3804…
remains failed after confirmed Replace/Resume and a30s disabled-Edit wait.
Independent R0c87accd0… proves valid managed2050/current authority; GET diagnostic0/
35bcc3ad… fully observes both original outcomes and enabled controls. The old
in-memory page state is lost; no app cause is established. Only fresh Pause/Reset
0/4dbc97db… in210.163s restores default/inactive and reloads all four originals,
with old2 bytes/results preserved. Previously unrun WebKit root0/abd3239d…/
351.370s and management0/89679218…/302.177s each pass four actions/five POSTs and
all ten preservation flags. No old aggregate is rewritten or full HOST/matrix
acceptance claimed; stale/concurrent revision and injection/timeout branches remain.
Rootless76 admin1 remains transport/browser1 in919.435s, SHA8f027823…: Library
locator404 console/read deadlines, no operation/POST/effect, all contexts closed
and preservation flags hold except its unaccepted scope. Admin2 remains1 in
301.809s/SHA5bdb14be…: abort/deadline and expected400-versus-actual422 assertions;
one pure config-validation422, zero accepted operations/effects, all closures and
other preservation flags hold. Ordinary workload3 now passes transport/browser0
in580.334236s, receipt SHA256
740d46ba58e35412a1cf78568e4adeb1f0223c60f9831d012c61dcc63b032428:
six cells/six UI callbacks each,12 pure UI validations, zero operations/effects,
all seven preservation flags and closures, maximum callback32.101s.35/36 UI body
captures succeed; one Chromium-management body remains unavailable, so no complete
wire-transfer claim.
Focused rootless tag19 passes0/231f8cc6… in479.852s: six cells/19 fresh callbacks
each,114 passes, maximum10.165s; each joins16 queries and three client refusals.
Zero POSTs/operations, all seven preservation flags/closures and strict console/
CSP checks pass. Split tag-provenance/bounds scope adds no full-case/matrix stamp
or completed-transfer claim. Earlier aggregate failures stay false.
Tag19 receipt SHA256231f8cc6c908314752c8dc458a1cdc205279cb3c67bace595e461444e995bba7.
The tracked test driver now replaces the overlong tag aggregate with19 named
45s callbacks; CATALOG-02 requires all19, with52 baseline assertion IDs and16
case mappings. Exact query/hash/settled-DOM and client-side no-request refusals
remain; no receipt import or timeout relaxation is added. Driver8cba6cd6…/
runner70b3a8fb… and the existing unit fixture's ID list are the only new test
changes. Existing Node metadata18 and Python functional-runner545 checks pass0;
the initial27 stale-fixture-ID failures stay retained. Ruff/ESLint/format/syntax
pass; no new full gate covers this test-only integration. Installed tools3855
and source76 runtime/UI are unchanged, ordinary/negative integration is pending.
Rootless configuration-negatives1 remains transport/browser1/1320d5a6… in699.559s:
five cells each pass25 callbacks/24 local refusals; WebKit-root times out on its
first10s Administration navigation click before config GET. Zero POSTs/operations,
strict health/all closures and all other preservation flags pass. Focused fresh
WebKit-root2 is running, not yet qualified; any later coverage must join original
five plus its actual result, retaining the failed aggregate. No server422 claim
comes from these local form refusals.
Native maintenance4 remains transport/browser1/fa102fc6… in1084.098s: seven UI
steps pass, publishing only the new903 copy's B/C/D pairs, each2files/4751B,
with four successful Sizings and three confirmed Applys. Apply-E original
7d6d6295954ab6087f8f1ec8bc344a2b fails20/HFAPI022 on protected policy inspection
timeout before helper handoff; it is not resubmitted. Read-only0d8be27c…/
cb8b2777… prove empty events, configuration-D/retention5 and no pending host or
configuration intent/application audit for that failed original. The UI correctly
fails closed under ADR154; no product defect is established. All browsers close,
with zero unexpected page/console/5xx errors, and the old ten publications,
worker reports, private originals, roles/keys/1722/Hub remain protected. E Sync,
retention reduction, prune and purge are unrun. Fresh-context M5 preparation is
for a distinct reviewed remaining workflow, not replay or a false M4 pass.
TARs4 preservation passes0/12807934… at same-host ROOT
`/var/tmp/web022-retained-public-source-tars4`: four completed public source6–9
TARs retain bytes/semantic metadata/old HOME aliases and88 producer/artifact
hashes. HOME276353024→346816512B/net70463488B; ROOT1975537664→1904615424B.
FIEMAP70660096 exclusive bytes remains separate from actual net free movement.
Source10–13 capture-only originals stay untouched; no VM/image/checkout/venv/
private-store cleanup, off-machine backup or lowered reserve occurs. WEB-022
and full85×18 remain open; check18 is historical to these new records.

Current batch exact receipts: configuration-negatives1 SHA256
1320d5a6166704d3b66f97c674bd20e1d669fb4b42dc7a4dc538df07173bf1ed;
maintenance4 SHA256fa102fc6a357b7cb41c230e40658a5e3fc0635b472b78bb54d962804586adc64;
Apply-E read-only SHA2560d8be27c80a1616eded4fbe374645fd3f35c41e24b5ebda6b3f6afbfc9483749
and events SHA256cb8b2777a7b0290657515a017ab8cb4f593929dba92d07ccc3ef115cb03a8412;
TARs4 SHA25612807934ba3d4a53923d26c5e45033e500430968b3059a970aa0e138c5bff2ed.
Focused Python log SHA256d2a0879f27a995702c4e90d2f91ede45ce4fcd8525edaf3acbff5046cd4b6790;
Node report retained at `web/.artifacts/functional-driver-3gDwMa/report.tap`.

Native maintenance1 stays1/6e15398a…/41.963s before POST on the outdated clean-
paragraph locator. Numbered2's pre-intent capacity refusal30089af6… remains;
after preservation its actual run fails1/3bedfaff…/41.378s at baseline4!==30.
Numbered3 also fails1/2c45b00c…/95.402s at baseline404!==200 with one console404.
Both send zero POSTs/operations/publications and close all contexts; old payloads/
stores/config/roles preserve. Observer/backend Stop remains unsealed pending
genuine maintenance success. No replay or app-cause claim follows.
Maintenance3 receipt SHA2562c45b00c0b06d02f942ad4660f665bce3f15734315ded9e3ecbe1ca7ee0c25a6.
Original3f SDK/pending/Stop and ec674 remain untouched. Driver16 mappings/52 baseline IDs/full85×18/CARD gaps stay open;
cheap check17 is historical to these newer facts.
Exact gate13 generated TMPDIR retirement passes0, receipt SHA256
1b7149eefe2461fca787461421ff0f9975b742eb63f73b1ee429afc45570fe25,
root2261377024→3172126720B; source/logs/results/inventories retained. Earlier five
root WEB006 dependency caches retire0/e72ef92e…/1422716928B/6912 protected hashes.
Later two root source13/14 caches retire0/56fd4000…/648273920B,2069 source/artifact
hashes and both virtualenvs preserved. Exact ONE completed HOME source21 fixture028
frontend dependency cache then retires0, receipt SHA256
c93f7fda060a83b94ebaf7ccac7beb63f6133b1693bb62b7b38973eb77e65993:
Home277278720→572784640B/net295505920B on the shared filesystem. FIEMAP separately
measures284188672 exclusive regular extent bytes/shared0/unclassified0; it is not
substituted for actual net free space. Fresh all-UID process/mount checks and6602
source/venv/artifact/log/alias/current/native14/API76/install-donor records preserve;
original preparation1 and receipt-bound preparation2 stay retained. No guest/VM/
image/service cleanup or reduced reserve occurs. Exact old source21 .venv
preparation refuses its >50MiB criterion: allocated89616384B but only3424256B
exclusive/86192128B shared, no deletion/protected change. Three public completed
source TARs15/19/21 instead preserve3/0, receipt SHA256
4d53b464a0ad9d85d0f4969d122d37e56c4e8f58392600dd40a00df910e712fa,
under same-host ROOT `/var/tmp/web022-retained-public-source-tars1`. Three original
HOME paths become verified symlinks; all63 source/UI/wheel/inventory hashes stay.
HOME278671360→331792384B/net53121024B, ROOT2481508352→2428108800B; FIEMAP's
53198848 exclusive regular extent bytes/shared0 is a separate observation.
Fresh all-UID checks/copy hashes/semantic metadata/fsync precede retirement of
only exact duplicate source TARs. Source checkouts/.venvs/VMs/images/guests stay
untouched; this is local ROOT preservation, not off-machine backup. Installed q
regression is qualified above; full85×18/positive controls remain open.

Four more completed public TARs22–25 preserve4/0/c99ad8a6… on this same host's
root `/var/tmp/web022-retained-public-source-tars2`:84 producer/artifact hashes,
original HOME aliases and bytes/semantic metadata retained. HOME270708736→
341733376B/net71024640B; ROOT2236841984→2165592064B. No VM/image/checkout/venv/
store/unknown-evidence moves or off-machine backup. Existing reserves stay fixed.
Four public fixture-projection TARs19/21/22/23 then preserve4/0/5fc485f6… at
same-host ROOT `/var/tmp/web022-retained-public-source-tars3`, with all100 producer/
artifact hashes, original HOME aliases, bytes and semantic metadata intact.
HOME257499136→328552448B/net71053312B; ROOT2153357312→2082168832B. FIEMAP70975488
exclusive bytes is separate from shared-filesystem free-space movement. No guest,
VM/image, checkout/.venv, private-state moves or off-machine backup.
Receipt SHA2565fc485f6753952c71d983f8cb4b76909af6a57e380c56a4da20fd96afc71e9d5.


Current source75 worker UI passes transport0/browser0/five steps in261.833791s,
`native75-corpus-jobs-clients1-reuse-result.json` SHA256
a65fcdaf628ea907b95d60a083071b417656f0d3210d0b737bf266530914f97c.
Full original2d3600e341779fb4859d35c6b378cbbd/run37523d22decc44c5bc7087522cb75cbe
is clean0 at4 repositories/10 publications/23 physical objects/41279B; revision9
original7327ab1adc6f7c1f865200fe80756a65/rundf47052330c5490dbcdf409aeadf7799 is
clean0 at1/1/8/6286B. Both original result/persisted report/UI/reload joins and
18 Library refreshes pass. All nine root proofs/closures/errors0 hold; old reports/
payloads stay exact and new full marker37523d22… survives revision verification.
Separate CLI/MCP receipt SHA256
ed69d8273ba9ad84ed3a316128533899f30c3821a72b632a2ba2a75caaab8e8b and detail
74cf7332907d83dd59fa265aaf8072c9f2533e283500bd65469ea7893b83fd0d prove four
CLI reader/writer status reads plus all14 MCP tools per prefix/28 calls pass0.
Both report tools join these genuine new full/revision reports, not seeded reports.
SAME CID39a277b6…/PID85053/start9596348 brackets actual Library refresh2→5.
Only the two original verification API/worker pairs, actual reports/catalog marker
and normal lock timestamps change; roles/original1722/Hub counter remain exact.
Scope is ONE source75 Chromium/root overlap cell; q fix remains uninstalled,
full85×18/client-matrix/mapped/CARD acceptance stays open, old failures protected.

2026-10-30 installed counter and rootless configuration acceptance: native75 C2
actually passes transport0/browser0/all5steps in
`.scratch/web-022-fresh-fixture2/native75-owned-model-c2-reuse-result.json`.
One distinct reviewed revisionC/max5 Apply and one Sync publish exactC pair
bfc3d11efd66419eb89f31a9483f7d7f/generation2,2files/4751B; Sync7340b353f0bb54941dccdefe503cd837
joins run9642b690034c49b187f1399b7fa6bae9. Visible published bytes4751, downloaded0,
reused4751 match the original result and persisted75 report. Exact Library,
README and Files checks pass. Root proves old private receipts/SDK/Stop/pending/
browser files/unselected archive and role/key/coordination state preserved;
only actual reused payload inodes gain one link/ctime from publication. The
copied/visually viewed run-report image `native75-c2-published-counter.png`
SHA256b2dba58fcfe10c2dbcd1bf3dad3520f4a0d744ba3ae061d40c5501eb1aa8596b
shows the actual4751 counters. Original74's wrong0 is retained, never rewritten.
C1 remains failed before any POST/operation/configuration effect on a test-locator
scope error; C2 explicitly qualifies that zero-effect closed state and fixes only
the locator/wait, preserving original evidence. D1 independently passes the same
actual4751/cached result/UI and exact publication workflow, pair7df8616d9aa14e00870597fece08c9dd/
generation3, Sync9b70ea9334ea70090555780c7e200193/runf38655dc32a24881af623fe43398dd77.
E1 also passes transport0/browser0/all5steps in
`native75-owned-model-e1-reuse-result.json` SHA256
426ce7e5f337946061b3bbb2f8d8bf27eaff65803c2f987d9fcebad542f715b0.
Actual E publication604d242556124f5facab9c783d951951/generation4 joins Sync
0acc8e645c0a13ba5ea85a0ebd12281f/run5c110a1076694cdb9d8c6c36762227e9:
2files/4751B, published/reused4751, downloaded0, exact UI and root preservation.

Native75 NEW/E2 passes transport0/browser0 in
`native75-verify-new-e2-reuse-result.json`, SHA256
fcb9255f04269ca5d3cb59cdc5346229d85ebbb024cde3f4722b2b8c74c6cf54.
Original operation2778cb00b5e341683210f3007e60a1a4/run
c79b70575552461c95fcd47ed35da7e0 verifies the actual E Sync run
5c110a1076694cdb9d8c6c36762227e9:1repository/1revision/2physical files/4751B,
clean0, visible result/stored75 report and same-original reload joined. All seven
root preservation predicates pass, including old full reports/last_full. Retained
C/D/E are context, not a three-revision or full-verification claim.

Retention/prune2 remains transport1/browser1: its first four steps and all four
original operations succeed, then the fifth bookmark expected-text assertion
fails; the collector also attempts to stat the now-pruned B manifest. Original
operations2be9937f7c50b0291307eff38274119f,3a3f1fad353524019abe2ad02ed73e27,
453256b89f3674983dc61f72460bcb81 and ee31a870117b436cde888616c3c77727 are not replayed.
`native75-original-prune2-readonly-qualification2-result.json` passes0, SHA256
6c1cc280d2e391f0726283c41ec59cf652b4e9cec782f52894fbd798475646e2:
B91bc is pruned, C/D/E and current E remain, original backups/history/stores/roles
are preserved, and only actual shared-payload nlink-minus1/ctime changes qualify.
It proves effects/preservation only; qualification1 and the full prune UI scenario
remain failed. Raw derived-index default overlays are not configuration authority.

GET-only READ1/2 both remain transport1/browser1 with closed contexts, zero POSTs
and all four state-preservation predicates true. READ1 races a transient null panel after explicit Select current; a role-locator
wait fixes only the test;
READ2 reaches actual explicit-E README then fails the unsupported supplementary
`GET /catalog/repositories?scope=configured` probe. Neither requires an app patch.
READ3 fixes only that probe to the supported catalog search and passes
transport0/browser0, `native75-post-prune-bookmark-read3-reuse-result.json` SHA256
0f887ebd9d1e974efcfd0e8138f11b7ffbaf373926b282a2a44fe08c82fd5cda.
Literal B retains typed409/HFVER008, warning and no latest/README/Files fallback;
explicit Select current restores actual E README. Configured search returns
three rows with false/false/true enablement, and visible Library badges agree.
All original handles/state remain exact, no POST is transmitted, and no original
failed prune/READ result is relabelled. Root copied and visually viewed READ2's
401415B explicit-E screenshot, SHA256
819614683ba8a5cfb3f14afb2e95d3c8465ae92dff2a5695affbc4b14c65128f;
that image's visual scope does not make READ2 a whole-scenario pass.

Fresh rootless74 UI2f passes transport0/browser0/all4cells in1374.355s,
`.scratch/web-022-rootless-fixture4/config-tags-ui2f-result1.json` SHA256
d63368e62a678c4a8985fe824d078b2e59b9d5eaf6dda440329e896268c2e071.
Actual Apply IDs are e12f319524c76ef235f95ec11fa7b44a (Firefox management),
2c1a8349535b737e490e653a6b165551 (WebKit root),
b0f7c6f6ce8e24fbd2ca2557968108d5 (WebKit management), and
2f47e3083388b5f840524951a86f8a54 (fresh Chromium management). Each passes stale409
and same-original reload/confirmed pendingfalse recovery. Root qualifies the
six-cell union with old passed Chromium/root75ca and Firefox/root0928; old failed
aggregates and the original closed managementB remain failed/unexecuted. Four
new tags are the only normalized config changes, operational fingerprint and all
old files/seed/roles/credentials/guard remain exact; no original POST is repeated.

Public rootless75 input pack/render passes0/2.491s in private emptyRO NAS shadow
as UID1000. `/var/tmp/web022-rootless-inputs13/rootless-inputs13-proof.json`
SHAe3515ab2254902962dc73c5ca283cba100c686d6e85709123c1ddbbeba1166cc
records manifestaf554b047e8ef87681fd8ceaafd6c7ec8f6250693df7188e6c4eace6ab07f68e,
TAR3,614,720B/SHA2b4ec03653e2fb2156fd32b437defdba1bd3a67740aa06d88cfbebef2f186f6f,
67inputs/77members. Existing API OCI is reused; no new environment/image build.
Default store and current main remain exact during packing. The4 authorized test
file advances are separately pinned; runtime/UI/packaging's other1002 source13
files are unchanged. Gate9 is explicitly historical for the new test source;
current full gate and Library driver acceptance remain incomplete.

Rootless75 public transfer passes0 in `public-source75-input-transfer-result1.json`.
Original drain-stage1 remains1 after stock bridge stop0. Independent normal-stop
proof plus switch2 confirms three old role containers normally stopped/removed;
their terminal container exit codes are **unobserved**, never inferred from default
systemd status fields. Other four inherited CIDs remain exact. Switch2 passes0,
`rootless75-switch2-result.json` SHA256
d28c79a572a307b781baa49dea5e4319edf4bfeb47106469ff57847d80bef85a:
selected75/manifestaf554b04, original global27:1790/RO and new actual guard80290/
start1443836/invocatione640089e1a3d4a13abcedac465e3ea3c; no repeated bridge stop.
Prepare2 remains failed after successfully labeling only nine new75 leaves, on
its incorrect versioned asset-root assumption. Prepare3 passes0, retaining the
canonical rootless `/opt/hfcache/ui` root and changing only its manifest field.
Root independently reviews actual proposal
729601233820ebd4422dcada7dd4341c69ff1176b3f65f7fa469d4c5f345b0ed in
`proposal75-root-review3.json`; configuration-only six permission values, active
bootstrap inodes, SELinux receipt and kernel remain unchanged.
`rootless75-helper-publish3-result.json` passes0, SHA256
24b21e45fb8ae8fab54e4f639dc5693e7084718d9d6bbd027ab65dd95433dca4:
helper81177/start1508268/invocation9ea93e0c24794affa575d7b28bbe4302.
`rootless75-helper-start-app3-result.json` also passes0, SHA256
55889ebf40718aea07ba1f1d7981a9439d98dbc68c098128e3c992302cd87ce1:
API81508/worker81415 use image257cef26, Caddy81500 retains imagefa2a5634;
all UID983, empty capabilities, no-new-privileges, seccomp and distinct container
SIDs/read-only roots. This is actual startup/confinement, not installed UI acceptance.
Original failures, old pending750b and all store/key/credential evidence remain.
The actual75 GET-only browser smoke now passes transport0/browser0/all six
Chromium/Firefox/WebKit root/management cells, closed and preserved, in
`readonly-ui1-source75-reuse-result1.json`, SHA256
4be4d88b4283a55fce7122a16a65a575a27541b14a8284ad72540d1ddb726804.
Administration/Library/exact Files/uncaptured README and metadata reads pass;
seeded reports are not installed75 worker-job proof. The separate
`client-library-window75-1-result1.json`, SHA256
1c416ae717e5ebcdb555fc47416c0f52854675d5d278289f2bd98f128617daf5,
passes both transports0 with18 Library refreshes/4 CLI status/28 MCP calls in
one Chromium/root window. It does not extend client overlap to all six cells.
Rootless corpus A1 later remains transport1 after normal stock bridge0, on an
immediate CID-removal observation race. Original result SHA256
ae2bd9b76c78067f3d70c148f63709c97b3252721a4cda6c3b3771a37ea4484f
and all four guest checkpoints stay. Independent readonly2 SHA256
84835310bf3e730c5108068d779c895efa2f314ea8c5e48f0d2965e8d1c338c8
confirms three role CIDs/PIDs gone, six retained stopped CIDs, helper81177/guard80290,
original1790/RO unchanged and no backing. A2 now passes0 under continuation2,
`rootless75-library-corpus1-prepare2-result.json` SHA256
7e4f9c8d5c601d6bd014d2de78c687be5f45fc68ff883873c629adec5b09acec,
without bridge-stop replay. Root independently reviews actual byte-identical
proposal729601233820ebd4422dcada7dd4341c69ff1176b3f65f7fa469d4c5f345b0ed;
review2 SHA2564fe2fbcab12fc37001fffb081081dafa357d3ce8497b22764ad914c5991452e0.
B2 also passes0, `rootless75-library-corpus1-activation2-result.json` SHA256
28dd09a9d933d74a4d862574367742a980344cf0b7a811f3a67990b7e9af7e52.
Same75 runs903118a5/28 configured/29 union/7 publications; original1790 stays held
by guard97114/start2072897/invocationa3b264a3e7874416bb5a787fdb803a49 on NFS-RO.
Helper97407/start2078365/invocation5fe9ac916f4b4321bfd7a6456aef266f and new
API97629/worker97545/Caddy97639 retain the selected artifacts/confinement and
configuration-only grants. Authority/server/credential writes remain zero; old
archive/stores/config/private evidence remain. Original A1 stays failed and the
retired app terminal codes remain unobserved. Rich-corpus pilot1 now remains
transport/browser1 in264.819s, result SHA256
1b645598d4095058715a86eae501f3c24110e7b12693b9949be648acb9dfec01:
first ten read steps pass, the last10s exact-base check fails with configuration
and host-status GETs still pending. Contexts close, zero POST/page/external/5xx
errors/effects and all four other root proofs hold; completion stays false.
Fresh rootless6v2 under3855 now passes transport0/browser0 in890.936866s,
`rootless75-library-corpus-six-cells2-reuse-result.json` SHA256
7f67223141c938812dc19cfa082def5fa60e8407c68aa4962661da1b53f25d0b.
All six engine/prefix cells pass all eleven steps,66 fresh Library/Files/README/
configuration reads; every context/browser/server closes, all five root proofs
pass and zero GET effects/page errors/external/5xx hold. Per-cell API observations
are351/353/355/357/352/355; configuration13.714/16.108/13.847/15.859/16.023/16.276s,
maximum step33.869s. Runtime/source13's other1002 files remain unchanged. This is
120s pilot aggregate/10s DOM/15s navigation scope, with no mapped-case/full85×18
stamp or new75 worker-job claim. Old rich pilot1 remains false; its failed-but-
closed prerequisite supplies closure only, with no copied passes. No UI run is active.

Existing never-active corpus packaging passes0 in privateRO NAS shadow/login1000.
`/var/tmp/w22-library-read-corpus-pack1/corpus-pack-result.json` SHA256
4dceb5dcfdabda86fb62d1577df3103fad0f681627f071f1f3dff86fef85af86
records TAR13,415B/152members, SHA256
52b16c363d17b8c7f04683307a64519b7cd1daa738a3882258f39403d2db221f.
Original154-entry/~89KB input, UUID903118a5-b93e-4fa6-aaf7-72d0fbecd832,
28 configured/29 union/7 retained publications and all original bytes/inodes stay.
Embedded example version1.0.0 and source-recovery version0.2.2 remain seeded
provenance, not genuine75 worker jobs. Public transfer passes0 in
`browser-read-corpus-public-transfer1-result.json`; no new VM/rootfs/browser copy.

Same-VM corpus activation now passes. Original A1
`native75-library-corpus1-prepare-result.json` remains transport1 after all four
normal drains0, on missing ControlGroup for an inactive timer; all14 original
checkpoints remain. No lock/export/backing/store/config effects precede that
failure. A2 continues from the actual drained state without repeating stops,
`native75-library-corpus1-prepare2-result.json` SHA256
8bd1dfb37f1b97421fa8c244d45548f189e0937f6417050656ec0cf11fa410ff,
transport0. Its actual proposal92dafa01399b19d9fd4f2bd17229cb82439b037c528f07affeb916019f931e6b
is byte-identical to existing authority,263 files/six grants unchanged; independent
`native75-library-corpus1-proposal-root-review1.json` SHA256
29323d07a9bdc57db7fe26fda9ff4a1803f6d5224a70d74afa94e96f7bddb3f3
reviews those actual bytes. B passes0 in
`native75-library-corpus1-activation-result.json`, SHA256
a65efad3af4d4a9a9bf1f832ca33c2daa89dc7a5889bf277358a14791ebde9bf.
Same75 runs the new903118a5 corpus on owned NFS with original27:1722 preserved;
old archive/stores/config and all protected evidence remain. Zero authority,
server or credential writes are needed. New helper/worker/API/Caddy PIDs are
64741/64769/64778/64789; seed report versions remain unchanged.

Actual current-driver Chromium/root pilot1 remains transport1/browser1 in
`native75-library-corpus-pilot1-reuse-result.json`, SHA256
5b36432851e835f7bedd203ea4aea01df500df8667e2fb2a5bbab7974980edee.
Its first three read steps pass; step4 tag-provenance/bounds hits the45s aggregate
deadline after27 confirmed query states. The remaining seven steps are unrun.
Zero POSTs/page errors/external requests/5xx and all preservation predicates pass;
the failed completion flag stays false. Numbered pilot2 also remains transport1/
browser1 in265.855s, `native75-library-corpus-pilot2-reuse-result.json` SHA256
eae3b42da22b7401f177a9ef966092fc775d091a84c9ab1c8475e496857cc26b.
First three steps pass; step4 reaches23 confirmed states through groups-AND0,
then a10s page wait times out. Its120s aggregate/driver/request limits and all
prior preservation flags remain; seven later steps are unrun. Focused
`native75-library-clear-diagnostic1-reuse-result.json` passes0, SHA256
8f19b67982e2e30d437b2e2e10664966033649ae4d4491d7b27fe3bfc9028e95:
actual same-browser initial526ms, AND-zero674ms and one Clear29 restoration840ms,
zero POST/page/external/5xx errors/effects and all root proofs. These observations
neither establish the earlier failure's cause nor complete eleven steps, a mapped
case or matrix acceptance. Actual pilot3 remains failed after nine passed steps;
the tenth checks before loading settles. Two readiness waits in the existing
`web/test/functional-api/driver.mjs` at pilot4 produced SHA256
07fe51d6a5fcc5b1b51becb739e3e8ba7fd77cd5e42e97c3f789aee1cf981eed.
Actual pilot4 then passes transport0/browser0/all eleven read steps in one
Chromium/root cell, without full profile/matrix acceptance or relabelling pilots1–3.
QA1 passes all three combined technical-filter checks and keyboard/filter
pagination. Its retained-tab focus observation fails before asynchronous
restoration; later checks are unrun. Actual QA2 remains transport/browser1,
receipt SHA256306600bb558fedf8fa0c9d3e65c8f8d599b5aff9389105b3d79ff91b12c0d1ce:
first six checks pass, including retained keyboard/README and390px layout; step7
cannot observe real200% zoom, later checks unrun. All contexts close, zero effects
and other root preservation predicates hold. Root copies and visually reviews
`native75-qa2-390px-files.png` (213875B), SHA256
b9e9f8cc466724757f89ca580c731f45572e52db3cab5a7e78e1d256633e6a28,
and `native75-qa2-390px-readme.png` (284886B), SHA256
38b46f000a16a5537273d9f145088df378af19ebe979291f095b36fa5bc15681.
Actual document/scroll widths are390/390px; the310px table scrolls624px content
by keyboard0→11, with3px focus outline. Images explicitly show metadata loading/
unobserved state; this is layout/keyboard evidence, not completed metadata proof.
Separate `native75-actual-browser-zoom1-reuse-result.json` now passes0 in16.762s,
SHA25633d9b0e6933e5f3647f4b8f7937577f1307e11b624d2d5c55588a0c9b613d759.
Actual browser Settings200% changes1440→720 CSS pixels and DPR1→2, retaining
outer1440/pinch scale1. Loaded Files layout,3px focus and contained table keyboard
scroll0→4 pass; Settings restores100%, closes normally and all five root proofs/
no effects pass. The small persistent profile remains. Root's screenshot review
qualifies the README claim: its region exists while the card is still Loading,
so fully loaded README layout is unproven. Reviewed README PNG187210B SHA256
6a7eb689761a51fa1924667ae2c4f52dfa3b269d14e1943f225d37fae0cc5e3b
and Files PNG196846B SHA256
c1fe4e6a8041a5affcea30257500037df47fd54fe12166d84096f3d11114f1fc
are720px wide at DPR2, an apparent full-page capture crop; no full README visual
acceptance follows. Raw zoom0 stays unchanged, QA2 stays false, and no prior six
passes/full case are copied. Native6 under driver07fe now completes transport/
browser1 in1026.820s, `native75-library-corpus-six-cells1-reuse-result.json`
SHA256c39f400e50208b1237088297c4707a4bde83ebf1de4affe799db1cef2b355140.
All six cells pass their first ten Library/Files/README steps; configuration passes
five cells, only Chromium/root's original10s exact-base wait false. Every context/
browser/server closes, with zero effects/errors/external/5xx and all four other
root proofs true; the six-cell completion flag remains false. No aggregate is
relabelled. A separate focused native Chromium/root configuration follow-up is
now passes0 to qualify that cell only, without repeating all six or relabelling
the original aggregate. Current full gate and85×18 remain open.

Separate zoom2 under current driver3855 passes0 in20.693s,
`native75-actual-browser-zoom2-reuse-result.json` SHA256573761954db1509b15d4a2033dc9260145f9c5a76afdff661ce172872774d01a.
Loaded exact README heading/GFM table/code use the same publication pair at100%/
200%;1440→720 CSS/DPR1→2/pinch scale1. Card475px/table+code433px fit with right
edge700<720; loaded Files431px/624px scrolls by real Arrow keys0→7 with3px focus.
All four viewport PNGs are1440×913 and cover the physical viewport. Root copies/
visually reviews the200% loaded README image114600B SHA256
8c23b03efc22e44ce1379d9a4ba61c173be08c76f12c8beb11433078c0ffc19f
and Files image124256B SHA256
41669362fabd2e6004a66c2d3c7a78f9aeec30ca9cfa76fd811a830336e6dda1.
Settings restores100%, context/browser close, all five root proofs/no effects
pass. This new loaded-layout evidence does not relabel zoom1's crop/Loading or
QA2's failed aggregate, and supplies no full-case/matrix stamp.

Gate10 fails early at types, inner/outer1, before tests/build; its result remains
`gate10-result.json`. Only two fixture typing lines change afterward, fixture
SHA2566ce33f05eb2e5e533bac9dbc2991de8f1962c1d116c1b4a539f69f68b5c75d24.
`source13-with-browser-tests-product-freeze2.json` still pins1006 files, exactly
four test-file changes/1002 unchanged. Required gate11 now passes inner0 in
2625.186s and outer0 in2626.031s, all1006 frozen files unchanged:9580 backend/
52 opt-in deselections,4049 combined frontend,581 Cockpit,16 wheel and two built-
browser fallback checks. `gate11-result.json` SHA256
c0176af893b9f10d609b3db391d004d41c8dc690bf27fa9058344f9a0606bd94
pins inner logc58bd0588260f247d6f65cb75ddb0812474c3b22cae7d164fc20e38e9fac45db;
`gate11-shadow1-result.json` SHA256
d051844840092c1ac7cb3355316914c36441d13616198a56a00e1a9c34c32da5
pins outer log70c52b30e63ee42c285a9a9def485a5892eb1cfae2ee67dbb2fe56db01035305.
Gate11 is actual0 against its prior source. Current driver SHA256
3855cebbc53e6a4bdad2b2cd5bf1fbc31a026c355334fad8f029471636137102
adds only a test HTTP-response listener35s before the unchanged10s exact-base DOM
wait; browser fetch30s with queue caveat and strict45s callback remain. No app
change follows. `source13-with-browser-config-response-wait-product-freeze4.json`
SHA2567ea363d2ef69d01d9ab01fda05e3f5d2e10151a55f865cb2174449adb94f9510
pins current source. The current full gate remains required: only the same four
test files differ from source13, its other1002 unchanged. Pilot4's one-
cell eleven-step pass does not complete installed85×18. Driver mappings remain16/
34 required steps, CARD-10/12 partial/unmapped; WEB-023–026 remain pending.
Prior cheap `agent-records-native75-check4-result.json` SHA256
7fb65ab87f6205abdfad5291e199694cd8b945468e8e734c5f1d5dcfcdc760d9
passes docs221/29 and9 plan tests/0.71s; shadow0. It predates this update and is
not the required current full gate.

Static preservation now completes3, `/var/tmp/web022-retained-native-builds1/result.json`
SHA256f63ba45294abbb56bac53c4591f4a25045d5f1ae001c60893098aeef97e30bef:
closed clean-release4/6/7 retain all bytes/semantic metadata on root and verified
original-path symlinks; only exact complete duplicates retire. Recorded Home free
258334720→378793984B, root1482280960→1361256448B, no guest/private-state changes.
Old125-report relocation/row126 both copies and untouched reports stay intact.
Retirement of exact completed GREEN gate11 `/var/tmp/.w22g11` now passes0,
`gate11-successful-temp-retirement-result1.json` SHA256
4761ff0f7274a3f3826484136a708aad08d065f06f0dbfbc195b32f8bf9ade5d.
All179508 generated entries are removed after full inventory/fresh reference
checks; gate logs/start/results/freeze and inventory remain. Root free rises
1349586944→2272735232B; no guest/source/release changes follow.
Old502885's original key is confirmed lost; its Apply/import outcome remains
unknown and untouched, as do other old VMs.

The present7 GET continuation completes the one-cell actual7-SHA/e6ad4b8a
read scope after qualification2, without replay. Distinct8/9 README revisions
remain later finite-Hub work. Keep known a88 scoped recovery/new-repository/
derived catalogs distinguished from both unknown sibling keep files, all seven
predecessor publication/card/ref/observation sets and old real state outside903.
No failed aggregate or full matrix is accepted by the scoped read success.

2026-10-30 actual native75 continuation: extraction1/A3/B3 prepare+independent
proposal review+publication/C3 all exit0, receipts `native13-*-result.json` in
`.scratch/web-022-fresh-fixture2/`. Proposal92dafa01 retains all helper bindings,
SELinux receiptfe124065 and six existing grants; installed sources and sync.py
join the indexed clean release13. Actual API56028/helper55998/worker56017/Caddy56038
run75 with original state/lock/key/CA preserved. A1 remains failed after its four
normal drains because its reader assumed all archive files have one hardlink;
readonly diagnosis proves two genuine blob/publication inode pairs, each nlink2.
A2 remains failed before creating work or performing effects on omitted socket
PID keys. A3 continues from the actual drained checkpoint, allows only those four
fixed paths/inodes/sizes/hashes and keeps all protected-file checks. No stop/job
is replayed and no failed result is relabelled.

The identified old74 Chromium/root document actually survives the upgrade and
passes transport0/browser0: real reload invitation, same document/no automatic
reload, visible unsaved RAM tag draft and both original verification handles
unchanged, no POST. `native75-oldpage-route08-qualified1.json` joins the actual
receipt and preservation proof to ROUTE-08; raw observer filenames/field
fullRELEASE08Accepted are a retained naming mistake, never RELEASE-08 Cockpit
absence evidence. Screenshot `native75-oldpage-version-notice.png` SHA256
2ddbb5e668286143763af684e468310ac0704e7bee879c4e083c268676d68ffe is copied and
visually viewed. This is one current native cell, not all18 acceptance.
Finite owned b/c/d/e Hub3 starts normally after the oldB listener's exact normal0
stop; `native75-multi-hub3-result1.json` passes0 and retains old inputs/evidence,
with all app roles/configuration/CA/archive unchanged. No new Sync/counter/prune
pass is credited from setup. Actual publication is next.

The reviewed Library/Files/README test additions are now applied to the existing
driver/extractor/fresh opt-in seed, with existing expectation updates. Receipt
`.scratch/web-022-validation/library-files-applied-format-expectations1.json`
records24 existing focused tests0/7.22s under privateRO NAS shadow/login1000,
Ruff/Prettier/ESLint/Node/diff checks0. Driver now requires34 steps and maps16 rows:
CATALOG-01/02/04/07 and CARD-11 are five new mappings, not browser passes.
CARD-10/12 stay partial and unmapped. Their fresh pre-activation constructor uses
rich=True/browser_reads=True; active retained archives are not modified into this
corpus. Gate9 predates these test-only edits; the final current-source gate and
actual browser pilot remain required. Cheap documentation alignment221/29 and
all9 test_web_plan checks pass after the preceding record update.

2026-10-30 source13/current execution checkpoint: actual required gate9
`scripts/check.sh --require-web --require-cockpit --with-build` exits0 in1943.444s:
9580 backend/52 opt-in deselections,4049 combined frontend,581 Cockpit and16
wheel smoke checks. All1006 frozen files remain unchanged. Receipt
`.scratch/web-022-validation/gate9-result.json` has log SHA256
`6be36795cb864c83a5e66046f5cb2730ae918eb8d3be05c83f0d1ef2b14d4d0c`.
The outer tool session separately exits143 after that complete inner0; its absent
completion record is retained. The distinct qualification
`gate9-wrapper143-qualified-postproof1.json` proves the complete log/result and
original NAS shadow/login1000 boundary; it does not relabel outer143.

The real native74 Sync's published_bytes0 for4751B is corrected by counting each
completed publication's logical manifest bytes. Focused12 and broad171 sync tests
pass, including reuse and post-publication cleanup/retention failures. Clean
auxiliary source13 `1e6de5054862e0b245f060f79de0996cb9ae5eea`, version0.2.75,
builds native release13/indexc6b54ddc/UI8287ecbf and API image257cef26 successfully;
main stays0.2.2. `/var/tmp/w22b13/build13-exit.json` and `build13-postproof.json`
retain native evidence. API build2, foundation and export each pass0, receipts
`/var/tmp/web022-api-source13-v75-build2/result.json`,
`/var/tmp/api75-foundation-controller1/result.json` and
`/var/tmp/api75-export-controller1/result.json`. OCI75 is66,297,344B/SHA256
`73e205011ec49811290e36f3f15cbbe9630d16e6dce875412ef0bd30614f2032`.
The failed API75 build1 preflight never launches a builder and remains failed.

Actual native74 jobs/clients3 passes two genuine full/revision verification jobs,
same-original reload,18 Library refreshes,4 CLI status reads and28 MCP calls
through the same Caddy/browser window. Receipts are
`.scratch/web-022-fresh-fixture2/native74-jobs-clients3-reuse-result1.json` and
`native74-cli-mcp3-result.json`. Rootless74 UI3 passes all six cells in
`.scratch/web-022-rootless-fixture4/guarded-workspaces-ui3-result1.json`:
12 explicit refused Doctor/prune-preview POSTs plus original-key GET404/unknown
recovery, with no repeated submission or inference of nonexecution. Pure Validate
diagnostic2 actually returns200 in21.813s with valid DOM and no effects; its
first attempt fails before browser start on one old output leaf's SELinux User
mismatch. Only that leaf's SELinux User is normalized, preserving type/MCS/DAC/
inode/bytes; both original failures remain. UI2f now runs four fresh configuration
cells, and native75 extraction passes0 before the normal A/B/C upgrade. An exact
GET-only old74 browser is READY with both real original verification handles and
one RAM-only draft; root owns the upgrade/go signal. No installed75 counter,
version-gate, UI2f or full85×18 acceptance is credited yet. Browser rootfs reuse
continues; the earlier20GB request is withdrawn. WEB-023–026 remain pending.

Latest installed runs: native73 UI6 passes all six browser/prefix cells and12
original full/revision verifications, GET estimates, rendered reports and same-
original reload. Its inherited doctor collector incorrectly froze the normal
verification catalog mtime/hash update; wrapper1 is retained and independent
`native73-jobs-reuse-qualified-postproof2.json` passes0, with all other original
files/roles/SDK pending/Stop and browser evidence preserved. No job was replayed.

Rootless73 UI2 passes both Chromium cells, then Firefox/root Apply
`750b5d2155ba66d066f3541589a844db` becomes interrupted after the protected helper's
deadline expires during `backup_ready` guard revalidation, before configuration
replacement. Original API receipt, staged candidate/history and pending inode
61497804 remain retained. Same-key outcome GET0 confirms `staged/pendingtrue`,
without changing the receipt or clearing pending. The captured config-preparation
fix removes two redundant nested validation rounds only within locked Apply;
public prepare and pre-pending/pre-exchange/post-install authority checks and
budgets remain mandatory. Focused527+54 checks and5 boundary regressions plus
Ruff/types/docs all pass0, recorded in
`.scratch/web-022-validation/captured-config-reconstruction-checks1.json`.
This local source proof alone does not establish installed fix acceptance.
Evidence: `.scratch/web-022-rootless-fixture3/config-tags-ui2-result1.json` and
the `config-ui2-firefox-*-readonly1.json` / `original-outcome-get1.json` records.
Same-original Firefox/root recovery now passes transport0/browser0. Actual UI
distinguishes API `interrupted`/`unknown · interrupted` from protected host
`staged/pendingtrue`, preserves the original key/ID and blocks new submissions.
Both protected-preservation flags pass: original staged pending/candidate/backup/
history/API receipt and all prior private files stay exact; inode61497804 remains.
Receipts are `config-ui2-original-recovery1-result.json` and
`ui2-recovery1-screenshot-copy1.json` in the same directory; copied screenshot
e61ac924…1249 is visually reviewed. Recovery does not settle the Apply.
Required gate8 passes0 in1902.967s under root's NAS shadow/login1000/nice10:
9574 backend/52 opt-in deselections,3708 web unit/4049 combined frontend,581
Cockpit and16 wheel checks. All1006 frozen product files remain unchanged.
`.scratch/web-022-validation/gate8-result.json` records log SHA256
`97aa79a75585d28cb15bcd1e1a6706f1dd14e275b8002a8d1b6523e4c5386570`.
Clean auxiliary source12 `739ab272e48edf481310d290dcab7b43b4206cb9`, version0.2.74,
now builds release12 successfully at `/var/tmp/w22b12/release`; numeric exit and
postproof are `/var/tmp/w22b12/build12-exit.json` and `build12-postproof.json`.
Its native index is `e5c2b3ad92eb17739551c43516f0b256e5b96fd9632e5f060796f8e24eba37bf`,
UI manifest `8598f06c2276d1431d803b54a70ad335f3bd6165d755a31df4812f277aa0122e`,
and wheel `ff4891af89f154618d6d08dba3ac28d8120811b63ba026de4d596692f3fa31cd`.
Main remains0.2.2. Canonical API74 image build passes0, producing
`sha256:d5f741cf3e43037dccf7a9bda940bd33fd116706a69b04fc8cb381d00a15a25f`;
receipt `/var/tmp/web022-api-source12-v74-build1/result.json` qualifies the isolated
RootFS storage configuration with Home read-only as donor and default catalogs/
contexts unchanged. The initializer independently passes0 in
`.scratch/web-022-validation/api74-rootfs-store-probe1-result.json`.
Actual foundation and OCI export now pass0, receipts
`/var/tmp/api74-foundation-controller1/result.json` and
`/var/tmp/api74-export-controller1/result.json`. Retained stopped-container proof
is cd9ef116…7b292; OCI `/var/tmp/api74.oci.tar` is66,300,928B,
SHA256`2439fcf64f4e61880c2d728e64b66f227fb703a101a3f218be36e87586ed602f`.
Pack12 render passes0: `.scratch/web-022-validation/rootless-inputs12-proof.json`
SHA25c72529…b2cd5, rootless manifest29a55b2c…37a33, archive0570d5c3…4f61f.
Native74A/B/C pass0 with proposal
`d1ba4f8dcd6b636ea0e13e5b4ccb653b6e1c7c744a75ae1f0c97e31ab6dd7e3e`;
both original bootstrap inodes/global27:1722/SDK/Stop/configuration/stores remain
retained. No new CA setup is claimed. Native74 UI7 now passes all six engine/alias
cells, transport0/browser0 in `native74-config-ui7-reuse-result1.json`: six tag Apply,
six stale409 refusals,12 plans/12 validations, and same-original reload/outcome
confirmed/pendingfalse without extra POSTs. Root proves six tags are the only TOML
change, fingerprint unchanged, and all old outcomes/stores/publications/catalog/
runs/browser files/inodes/roles/global1722 exact. This is one configuration batch,
not full-matrix acceptance.
Fresh4 launch and initial inventory2 pass0 on boot9cac37cb/DMI62e6d602; failed
inventory1 inherited an inaccessible cwd and remains retained. Public transfer/
seed stage/NFS-ro and same-profile74 prepare/select pass0, artifact indexddddfc55…6eb87,
archive37e4505c-e0a5-445d-ae93-ee55ecd82f18. New original27:1790 remains under guard
3448/start99803/inv9ec1894b on the same RO mount; its process SID is
`unconfined_service_t`, not a dedicated guard-domain claim. Helper inventory1 and
canonical proposal0 are actual; bootstrap wrapper1 remains failed solely at its
final receipt-atime check. Both predecessor module inodes, seven unchanged helpers,
labels/kernel/receipt are retained. `helper-bootstrap-fixed-metadata-readonly1.json`
proves only that receipt read-atime changed. The distinct qualified postproof now
passes0; root separately reviews proposal40f58da9…3d261, then helper publication/
start0 and app start0 retain the same guard/RO boundary. Original wrapper1 stays
false, with no bootstrap replay or atime restoration. Actual helper4222 and
API4515/worker4418/Caddy4512 are bound to their original start/namespace records.
UI2 `config-tags-ui2-result1.json` is transport0/browser1: Chromium/root passes.
Management Applyc4cc2ff9…f8a8d has an actual ordinary keyed GET200/confirmed DOM;
the next supplementary collector GET aborts at15s before the SPA's automatic fresh
configuration load settles. This is not an observed product failure. Independent
API/result and sealed-outcome reads prove succeeded/confirmed/pendingfalse and both
new tags; controller preservation/fingerprint checks pass. No Apply is replayed.
Same-original management A GET recovery now passes: confirmed/pendingfalse, exact
saved key, unchanged receipt/private inputs, zero additional POSTs. UI2b also passes
Firefox/root's full cycle, then stops before any management POST. UI2d transport0/
browser1 also stops before any POST/tag/admission, with preservation exact. Its
supplementary15s GET budget differs from production ApiClient30s; subsequent idle
configuration GET200/13.402s establishes no product defect. Both false runs remain.
UI2e is now running in session61168, the same three untouched cells with one30s
supplementary GET attempt and elapsed/timeout records; no pass is credited. Original
B's closed RAM draft remains unexecuted; the separate fresh management A/B pair and
UI3 require successful UI2e closure, preserving all original handles.
Native normal-start continuation3 passes0, with earlier failures retained. After
original-handle observation, actual Syncc2754ce5…1bd32 publishes2files/4751B and
Capture3 passes transport0/browser0/all4 steps, exactly one new Capture/no Sync replay
in `native74-owned-positive1-continuation3-result.json`. Root visually reviews exact
Overview/Card and Files screenshots, receipt `native74-card-files-screenshot-copy1.json`:
inert README code/omitted image, exact publication/file hashes/tags/readable table,
with integrity correctly Not observed. This is partial actual UI evidence.
The original Sync's published-byte total0 is a known installed74 accounting defect;
main now counts completed manifest logical sizes independently of download/hash/
reuse/final status. Focused12 and entire two-file171 tests pass in a private NAS
shadow, receipt `sync-published-bytes-broad-shadow1-result.json`; source13's exact
three-file correction is frozen while required gate9 runs. Gate9/new installed
counter acceptance is pending; original artifacts/reports are never rewritten.
No forced stop or SDK/Stop replay occurs. Exact records are
under `.scratch/web-022-rootless-fixture4/`; no old VM/unknown state is changed.
Separate public-report preservation safely stops after125 entries at a `/proc`
exit race before126 unlink, retaining both copies126 and the remaining56 untouched;
qualified postproof1 does not
relabel the original partial exit. No20GB copy, migration or reboot occurs.
Installed74 application acceptance/full85×18 remain incomplete; original750b5d21
is never settled or replayed by these packaging/installation results.

Actual rootless keyboard/mobile/reduced-motion UI4 passes transport0/browser0 in
all six cells: skip/main focus, keyboard Library/model tabs/history,390px navigation/
overflow and sampled reduced-motion CSS. Root preservation flags pass; copied
mobile screenshot3b4c20c5…dc4a is visually reviewed. Evidence is
`keyboard-mobile-ui4-result1.json` and `ui4-mobile-screenshot-copy1.json` under
`.scratch/web-022-rootless-fixture3/`.
UI3's original transport0/browser1 retains both Chromium passes and Firefox/root's
HTTP403 followed by a premature collector prepared-versus-uncertain comparison.
UI3b now passes transport0/browser0 in all four selected continuation cells, with
7 new403 POSTs: fresh Firefox/root maintenance plus both ordinary flows in the
other three cells. The original Firefox/root doctor key is restored and observed
through GET404/`unknown · history missing`, with no doctor re-POST; missing history
does not prove nonexecution and its original403 DOM remains unobserved. The two
original Chromium cells join only with that explicit Firefox limitation. Receipts
are `guarded-workspaces-ui3-result1.json` and `guarded-workspaces-ui3b-result1.json`;
all old evidence/seed/configuration/candidate/pending/API receipts/roles/guard stay
exact. No original operation is cleared or replayed. Full85×18/task completion stay
open.

One subsequent actual Chromium/root Library window completes18 refreshes with
browserExit0, zero page errors/non-GET/cross-origin requests or failed responses.
Four CLI status reads and all14 MCP tools at both aliases pass0 while the same
original browser remains live, bracketed at refresh counts1→4. This proves one
concurrent cell only; seeded report retrieval supplies no new worker verification.
The initial reuse attempt exits125 before UI because four root-created collector
leaves have the wrong SELinux User component. Only those four output leaves are
normalized to the existing work context `system_u:object_r:container_file_t:s0`,
retaining type/MCS and old metadata; no policy or application path changes.
The next wrapper1 compares the active `client-window` directory's mutable size/
mtime. Independent qualified postproof0 confirms exactly those two fields changed,
all old evidence files and seed/configuration/credentials/roles/guard remain exact,
and actual browser/client exits are0. Original failures stay retained; successful
clients are not rerun. Receipts under `.scratch/web-022-rootless-fixture3/` are
`client-library-window1-result.json`, `browser-root-collector-labels1-result.json`,
`client-library-window1b-result.json` and
`client-library-window1b-qualified-postproof1.json`. Six-cell concurrency and the
full85×18 matrix remain open. UI2's later interrupted Apply and same-original
recovery are qualified above; its remaining cells stay uncredited.

Fresh3 helper/bootstrap/proposal and publication now pass0. Exactly the changed
host_policy.py predecessor inode is retained; the other eight bootstrap files,
CIL/module/kernel and15-role receipt4b4d338b remain exact. Three recreated engine
coordination leaves receive their persisted types, two fixed runtime parents are
provisioned and nine selected physical bin/unit targets get narrow contexts.
Root independently joins83 source/rendered members, canonical stage modes and18
bindings plus exact artifact-index closure before publishing deploymenta54cc09e
and policy77c9e3ee, retaining configuration-only permissions. Helper3741/
start244700/inv34f38807 is actually confined to hfcache_host_helper_t with root
UID/GID0, capsC0 and empty ambient/inheritable sets, NNP1/seccomp2.

The original bridge command passes0 but its immediate collector1 races API/Caddy
creation. A separate read-only steady observation0, without restart, proves
API3976/start261415/CIDf7e7e6cf, worker3902/start260928/CID0aeb8f4e and
Caddy3984/start261421/CID1c3b8b70 running exact API14/Caddyfa2. All have host983,
caps0, NNP1/seccomp2 and separate container_t MCS contexts. Actual user-unit
invocations are a20e900d/4e46e00a/cef0ea13; unit MainPIDs are conmon/launchers,
distinct from these measured container-init PIDs. Guard3325/global27:1752,
original key/configuration guard and inactive calendars/SDK remain unchanged.
Receipts: `helper-bootstrap-proposal-result1.json`, `proposal-root-review1.json`,
`helper-publication-start1.json`, `application-start1.json`,
`first-start-readonly-diagnostic1.json` and `application-steady-readonly1.json`.

Actual readonly UI1 retains browser1/transport0: first Chromium/root reaches
Administration with GET200/no page errors but its collector incorrectly expects
an observed sentinel ID on an RO initialization inspection. Independent trusted
GETs prove exact HFMNT004/domain20 and NFS-ro; configured identity/status/host
binding remaina88ba17d, with three readable repositories and retained findings.
UI1b corrects only that closed qualification, then passes Administration/guarded
controls and Library filters before its byte-format assertion fails on the
correct human display4,288 versus expected4288. Both failures and all original
seed/configuration/credential/operation state remain retained; no POST occurs.

After the user's disk-space challenge, testing reuses the exact known-stopped
read-only browser rootfs/CIDc1e9314b rather than making another VFS copy. Prior
full inspect state, script inodes, reports and screenshots remain preserved;
each continuation uses fresh contexts and a separate artifact directory. The
first reuse interval changes root free space by about2.56MB, not a GB-scale
copy. New-container creation still retains its1,062,260,736B guard; reuse has a
separate512MiB incremental reserve based on no rootfs allocation,128MiB artifacts,
32MiB engine metadata and256MiB host/VM reserve. No permission or security setting
changes. UI1c now passes transport0/browser0 in all three engines at both aliases,
using the same runtime and fresh `/work/ui1c` output. Actual Administration/guarded
controls, Library, exact Files, uncaptured README and metadata reads pass in all
six cells, with zero page errors, non-GET/cross-origin requests or failed responses.
The observed UI1c root-space delta is~15.27MB; no new browser rootfs is created.
Original failed-work inodes/bytes and seed/configuration/credentials/roles/guard
remain exact. Exact files are under `.scratch/web-022-rootless-fixture3/`:
`readonly-ui1c-reuse-result1.json` and `ui1c-screenshot-copy1.json`, alongside the
retained `readonly-ui1-result.json`, diagnostic GET records,
`readonly-ui1b-reuse-result1.json` and numbered intents/results. All product files
remain unchanged. This six-cell read-only pass does not close the full85×18 matrix
or WEB-022.

At the earlier launch checkpoint, fresh rootless fixture3 canonically selects
0.2.73 before browser testing. Actual QEMU1229484/start25306657 is bound
to hostboot5cdab6b9, argv2ba2d8c6, new rootFS thin disk
`/var/tmp/web-022-rootless-fixture3/guest.qcow2`, read-only pre-recovery8 backing,
restricted loopback SSH46324 and DMI92a64f69-c6ba-4354-bd75-96125bbe3e2a.
Actual guest boot iseb0b5364-a7f3-473c-be74-d7888c87a7ee, SELinux enforcing,
UID/GID983, stock rootless overlay/default graph/runroots and original user
manager1208/invocation9ff507eb. Initial system/user app/timer roles are inactive
and four inherited containers are stopped/PID0. Older VMs remain untouched.
Public source transfer/extraction/API14 import passes0; actual cached Caddyfa2
is rejoined. Existing rich seed produces new archivea88ba17d-a263-434c-bf03-9bc125d4fa7c,
107 verified UID/GID983 members; pending05369a61 and two unknown siblings remain.
They are synthetic inputs, not installed reports or recovery acceptance.

Owned loopback NFS-ro/bootstrap passes0 without archive init or manual `/srv`
writes. First canonical new-boot global27:1752 receives its required coordination
label and guard2771 holds its original FD. Same-profile prepare/stage then passes0,
retaining nine mutable original roots/inodes and old stores privately, key61259513/
configuration guard61244163 and credentials in place, all old releases intact.
Three stopped role containers are renamed by exact CID without remove/replace;
their complete inspect specifications/history remain identical except Name.
Root independently rejoins original metadata and old API/verifier lock hashes.
Canonical switch passes0/4.61s with normal pidfd-bound guard handoff, same original
FD/NFS-ro continuous and no competing parent flock. Current guard3325/
invocation8d1eea5ec0754511928f15bbcdd3d905 is active; apps/helper/calendars remain
inactive pending selected bootstrap/label/index/policy provisioning. Configuration
permission remains true and the other five remain false; no grant expansion.
Evidence is in `.scratch/web-022-rootless-fixture3/`: `owner-verified1.json`,
`initial-{guest-readonly1,executor-private-state-inventory1}.json`, public transfer/
import/seed records, `ro-storage-provision1.json`,
`prepare-rootless73-{result1,root-review1}.json` and `select-rootless73-result1.json`.
The first private-cwd read-only engine diagnostic refusal remains separate;
corrected accessible-cwd observation0 supplies actual guard/container facts.
Full85×18 and WEB-022 completion remain open.

Latest prerequisite checkpoint: canonical unchanged source11/version73 API14
build passes0 in16.03s with child0022. Actual image is
`sha256:098329874304e2ee870816ffeba469e1dd1844bedfbf6d32032f82523a54d60e`;
log SHA256321e878e9aeb7a49844f4d37512789e70e22d48bf69fc5f86c4abd58bfaaf367.
One-second capacity samples observe home minimum394,797,056B, not an exact
engine peak. Export passes0:66,301,440B, SHA256
82bbbd2e7520c2ffd8b07d802d62c1b8c9af288915bc2beab8014b8fe9957dd6.
Actual foundation passes0/15.18s: UID/GID981, PID1, caps0, NNP/seccomp/read-only/
network-none, pinned base prefix, required native imports and no package managers,
Node, compilers or browsers. Stopped container6ac8ee7a and proof9135f4f5 remain.
Receipts are `.scratch/web-022-validation/container-build14-{exit,postproof}.json`,
`api14-oci-export1.json`, `api14-foundation1-result.json` and
`/var/tmp/web022-api14-foundation1/proof.json`. API11/12/13 failures stay separate.
Rootless inputs11 pack/render passes0 from those explicit successful receipts:
manifest9458d0083307d9490d2759b72fc391b9e31af10f1d9ba3b3f416d04daf55d1c4,
archiveb3790387e1e89df561d49f2a8f29609cab40872f38400fc010f7cc4ca52622b8;
`rootless-inputs11-proof.json` records exact provenance. Fresh target3 is still
prepared only until actual launch/ownership observation; no rootless UI pass yet.

Safe space work additionally retires only the three successful WEB-021 final
16-smoke temporary trees, with full inventories/test-wheel bytes/logs retained;
home426,119,168→721,764,352B. Receipt is
`/var/tmp/web022-retired-successful-web021-wheel-temps1/result.json`.
Four completed public build trees then move home→root, preserving full bytes,
mode/UID/GID/mtime/xattrs/symlinks and original-path aliases. New inodes are
explicitly recorded; no failed fixture or operation state is removed. Receipt
`/var/tmp/web022-retained-public-build-trees9/result.json` passes0. The first
older success-record-format preflight fails before copy/removal and stays retained.
Native73 same boot/four original role identities remain active in
`native11-after-api13-space-readonly1.json`; no application submission/replay.

Static build-file sharing now passes0:66 kernel operations share2,026,254,336
aligned duplicate bytes across70 retained Python/pyrefly/Ruff files. Privileged
reference inspection passes; full hashes/inodes/owners/modes/timestamps/xattrs
remain identical and no file is deleted. Exact candidates/FIEMAP evidence are
`static-runtime-duplicate-candidates1.json` and
`static-runtime-fiemap-candidates2.json` in `.scratch/web-022-validation/`;
single-use execution is `/var/tmp/web022-static-build-file-sharing1/result.json`.
Root free space rises to3,074,498,560B, home remains427,642,880B. This preserves
failed build inputs and all original evidence while recovering physical space.

Latest resource checkpoint: five completed auxiliary build environments and five
tracked-clean old worktrees retire normally after preserved inventories, exact
source/artifact joins, retained Git refs and privileged no-reference checks.
Receipts are `/var/tmp/web022-retired-successful-build-envs2/result.json` and
`/var/tmp/web022-retired-old-build-worktrees2/result.json`; root gains about158MB
and home228MB. Main/current source11 and all failed fixtures remain intact.
API13 then observes every expected cache hit, but fails1 while committing/importing
the final virtualenv layer. The single-copy allowance omitted import staging;
postfailure free space does not establish the actual transient peak. No successful
image or foundation is claimed. Original
`container-build13-{command,inputs,preflight1,process,exit}.json` and log remain in
`.scratch/web-022-validation/`; log SHA256 is
bc66cf3fabe0563a7b4e23cc2e92df4460c3fd12c7a76f081673ffe675c8ad06.
Further retries require an allowance for actual commit/import peak space.
Read-only resource investigation continues; no guest/service changes follow.

Native73 Diagnostics UI5 now passes actual wrapper0/browser0 in all six
engine/alias cells,12 distinct original UI POSTs. Each mode renders and joins all17
checks to its original failed-domain result/exit20/HFHUB002: offline hub_tls fails,
hub_identity stays skipped; read-only skips4 write checks and temporary-probe mode
passes those4 actual NFS capability exercises. Same-key/ID reload/Observe passes,
archive doctor report absence remains correctly404/HFARG004, initialized inspection
and zero probe leftovers return after every mode. Root proves .store/health empty
before/after with original inode/mode/owner/SID, published/run-report/config/SDK/
Stop/old API+verifier+host/configuration records exact, current four role tuples
unchanged. No existing operation is replayed; the12 new doctor results stay retained.
Evidence `native11-diagnostics-ui5.json`, SHA256
28a8d93ce8bf758d5d78bdb796ed32b4fff55cf79e989de21713c4fe966c601c;
private originals are in guest `web022-native11-diagnostics-ui5/private-diagnostics`.
This proves honest offline classification/UI/probe cleanup, not Hub connectivity.
Current human guide already explains skipped/failure/absent-report distinctions;
explicit doctor examples are optional clarity improvements for human acceptance.

Rootless prerequisite remains open: canonical API11 image build0/34.41s produces
a5ab6bc7 and exact66,300,928B OCI export3213ed52, but actual foundation1 fails1
before Python exec. The ignored controller's0077 build umask left extracted
interpreter dirs0700; executable leaf was0755. Failed image/export/context/named
foundation remain intact. Same source11/recipe/runtime-hardening API12 uses only
child0022 (parent evidence0077) and normal755 directories, but the canonical final
COPY of .venv hits host-home ENOSPC. Controller exits1 while writing its final
receipt; no numeric child exit or complete API12 image is claimed. Full build log,
context, partial layers/working containers remain preserved. No new build starts
until measured capacity is sufficient. No usable API73 foundation is yet proved.

Authorized standard UV cache cleanup4 immediately restores home28,672→127,692,800B;
only removable download cache goes. All installed source/main/tool environments
remain. Completed disposable successful cachewarm1 environment is separately
retired after privileged no-reference proof and preserved public requirements/cfg,
full inventory/success receipts, recovering home125,898,752→213,450,752B.
Evidence `/var/tmp/web022-cache-clean4-after-api12-space/result.json` and
`/var/tmp/web022-retired-successful-cachewarm1-1/result.json`. Rewarm exact locked
resolver cache before any next offline full gate; prior gate7 remains valid for
its original unchanged1006-file snapshot. Read-only post-space guest observation0
confirms native73 original four PIDs/invocations still active on the same boot.
Readonly system survey finds VG-free0/no spare disk; no VM/production/NAS change.
Fresh rootless fixture3 launcher/input packer are prepared only, with no disk/boot,
requiring real successful API export/foundation and unchanged browser reserve.
Resource analysis found conditional same-byte current API11/12 .so sharing66.4MB,
but the failed layers are still mounted: no kernel/engine change has occurred.
Full85×18 acceptance and WEB-022 completion remain open.

Installed source11/version0.2.73 now passes reproducible backend/UI build0
(13.35s),18 indexed artifacts and public native transfer0. Clean commit is
`d42aedfb99d851986e75c9a6a4be629739a207e9`; native index is
`08f150b512e87580b7de3cb61bbcfa63cf305a0b805ecb12db5885f7083bc3d6`,
UI manifest `5468a37690fd554903daceffbef50bb77657338995ca0cad8340b98462f644c1`.
Full native snapshot53cc6979 differs correctly from UI snapshot62f6812d; wire97cd0bef.
Main index/version/environment/product files stay unchanged.

Owned fixture2 normal upgrade A4 passes0 in80.89s: original four roles drain,
original27:1722 FD/owned NFS-ro protects stock native stage/switch, and measured
ROguard25397 starts. Earlier A2 missing bundle-member and A3 durable-pre-clear
pending assumptions fail before any service effects; both are retained. Private
Stop record pending=True is historical durable content; current marker is absent
and the accepted public outcome remains confirmed/pendingfalse/exit_confirmed.
Do not rewrite/replay that record. B's copied-helper rename error likewise fails
before effects and is retained. Corrected B2 prepare/publication both pass0;
root review independently joins19 bindings and162 source/artifact members of263
authority files to clean inputs. Exact deployment proposal is333f66a42686da92bbee0dca4cbac87baf857ff76c76c47e7a51635b1976923d.
Only server.web asset root/hash and deployment/policy bindings change; original
server/index/policy inodes are retained privately, helpers9/key/receipt/grants stay
exact. C1 preflight's invented full directory context fails before guard effects;
actual empty root-owned directory has unchanged unconfined_u systemd-unit SID.
C2 then passes0: normal original guard drain, same-lock owned loopback NFS-rw
handoff and stock helper25848/worker25868/API25879/Caddy25889 startup, caps/NNP/
seccomp/SIDs measured. Native API/worker remain unconfined_service_t; no dedicated
native SID claim. Original SDK pending, config/tags, API/verifier/history, six Apply
and six verification records remain exact; SDK/job/Stop/Apply submissions0.
Both calendars/guard are inactive, original global27:1722 free. SSL_CERT_FILE is
measured absent, not added. Root-reviewed receipts are
`native11-phaseA4-result.json`, `native11-phaseB2-{prepare,publish}-result.json`,
`native11-proposal-root-review1.json` and `native11-phaseC2-result.json` under
`.scratch/web-022-fresh-fixture2/`. Guest private phase records remain under
`/root/web022-native11/upgrade-phase{A,B,C}1/`.

Actual six-cell Administration UI4c now passes wrapper0/browser0 in all three
engines at root and `/management`: initialized archive/API-ready/policy-valid,
correct separate software identities, shipped schedule, inactive original observer/
verification timer and both bounded journal views. There are zero page errors,
non-GET/cross-origin/5xx requests and every original private/config record is exact.
The actual installed archive-classification fix is confirmed in all six native
cells. Evidence is `native11-administration-reads-ui4c.json`; source SHA is
2d81ac4f2d84d4f8c0a07b7670d18a174f4f003858036f181b3cf693bb2198f8.
Chromium/root health and schedule screenshots are copied and visually inspected;
`native11-ui4c-screenshot-copy1.json` records their exact hashes. Its first
host attempt refuses the unchanged capacity guard before any browser launch;
completed native11 TAR is then preserved at `/var/tmp/web022-retained-native11-tar6/`
with full bytes/metadata/original-path symlink, raising home1047044096→1082728448B.
No failed fixture or operation evidence is removed. Browser source and launch
inputs retain separate indexed UI/native snapshots. This six-cell native Administration result does not close full85×18 acceptance.
Next actual native Diagnostics UI walkthrough and economical owned rootless target/
image prerequisites are being prepared; no new product/harness feature is started.

Runtime conformance fix is implemented and frozen: archive/init168 tests and
API reads16 tests pass, including populated initialized layouts and retained
unknown/symlink refusals. The reviewed archive source pin is renewed; regenerated
browser IR differs only in source_digest320c5fb1→97cd0bef, with definitions,
semantics, routes and result shapes identical. ADR145 records that review.
Required gate4 refuses the changed source pin before tests; gate5 refuses an
agent-only work-package label in the ADR before tests. Both failures are retained
and corrected. Gate6 then passes9569 backend tests/52 opt-in deselections and
builds the wheel, but exits1 because the offline installation check needs index
cache entries removed by the authorized cache cleanup. All1006 frozen product
files remain unchanged. Current locked, hash-verified resolver inputs are restored
in separate disposable environment `/home/tyler/w22-cachewarm1`; unchanged offline
three-profile installation precheck2 passes0 in19.62s. Full required gate7 now
passes0 in1637.91s:9569 backend/52 opt-in deselections,3708 web unit/4049 combined
frontend,581 Cockpit and16 wheel smoke tests. All1006 product files stay unchanged;
coverage is95.02% lines/90.16% branches. Log SHA256 is
`3659aa84266c0433b36c05cd34aefee8cb7e8d5e2092e43d6d13b17cad4e1bb2`.
Evidence is `.scratch/web-022-validation/gate7-{start,result}.json` and `gate7.log`.
Only its successful generated pytest temporaries are retired after exact no-live-
reference proof;582728938 ordinary bytes are removed, with all gate records kept.
Failed gates/fixtures stay retained. Clean source11/version0.2.73 preparation,
reproducible build and actual installed Administration walkthrough follow this
complete green gate. Thin ignored upgrade scripts are prepared for root review;
no guest upgrade or product edit has occurred yet.

The user additionally directs finding safe reclaimable system space. Standard
uv/pnpm/DNF cache maintenance is recorded under `.scratch/web-022-validation/`.
`exported-user1000-image-retirement1/execution.json` passes0:17 known completed
proof containers and54 explicitly exported/runtime-ancestor image records retire
through normal Podman without force/prune; all other images/containers,29 external
Buildah objects and all nine verified exports remain unchanged. Root-only
CPR-cache deduplication2 also passes0:97 kernel dedupe ranges share1187840000B
while every original file hash/inode/owner/mode/link count/atime/mtime/ctime/
xattr and protected parent stays unchanged. No profile file is removed or linked;
operation databases, small private handles, VMs and production UID981 remain
untouched. Exact private proof is `cpr-cache-dedupe1/execution2/result.json`.
Measured after deduplication: root1454354432B/home1752588288B; warming the
current dependency closure subsequently uses some home space. Failed/unknown
fixtures and every original operation handle remain retained.

Selected application fix after UI4 diagnosis: normal durable catalog files,
completed transaction journals and run reports are misclassified as unknown by
initialized-layout inspection, producing unusable/HFMNT014. Architecture5.1/7.8,
FS-16/17/19 and decision029 already require acceptance of normal managed contents
and strict unknown/symlink refusals. Align implementation with that existing
contract, with closed initialized-only recognition, unchanged bounds and focused
archive/API-health regressions. Do not waive unusable as healthy acceptance or
alter the fixture. The actual UI correctly displays the backend result. UI4b's
subsequent wrong UI-source-snapshot expectation is separate: pinned UI manifest
b26d4419 carries UI snapshotf21678c3, while native index carries snapshota42f125d.
Keep these identity domains distinct. Both zero-POST failed runs/configuration/
SDK/Stop evidence are retained; new installed validation follows the runtime fix.

Administration UI4's first Chromium/root run exits1 with zero non-GET requests:
status/health/version reads return200, but the check incorrectly expects an
initialized inspection. Actual trusted `native10-ui4-health-diagnostic1.json`
shows daemon ready/policy valid and archive inspection unusable, with all required
directories present/NFS-rw and twelve retained catalog/report/completed-transaction
files listed as unknown. Full verification and status health remain independent
clean observations. The failed UI4 browser/work and unchanged configuration/
SDK/Stop records are retained. UI4b is running as host session59013, fresh work
`/home/webfixture/web022-native10-administration-reads-ui4b`; it explicitly checks
the actual unusable inspection alongside readiness, never initialized-state or
integrity acceptance. A read-only contract review is investigating that backend
classification; no fixture, source behavior, bound or authority is changed.

Latest UI3b terminal checkpoint: actual browser exits0 and all six tag Apply/
stale-draft cells pass. The host wrapper exits1 on its raw TOML dictionary
comparison because canonical reconstruction emits default fields that the
minimal input omitted. No Apply is repeated and the failed wrapper is retained.
`native10-config-tags-ui3b-normalized-postproof1.json` exits0: the installed
ApplicationConfig model proves every normalized field except the six exact added
model tags unchanged, including protected Hub values; fingerprint02f18a10 is
unchanged. All six original A receipts are succeeded with confirmed/pendingfalse
host outcomes; all six prepared B requests are409 with retained old base/draft
and retired UI readiness. Original SDK pending/Stop/API/browser records and
helper3790/worker4435/API4438/Caddy3826 are unchanged. Never rerun those six
accepted applications. This is qualified browser0 plus independent postproof0,
not an overwritten wrapper0. Read-only Administration UI4 is the next walkthrough.

Three human guides now clarify the exercised UI: recover an original host outcome
when restored history blocks Submit, use Compare before explicitly reloading a
dirty stale draft, and retain a key plus any known ID/receipt because a refused
Apply may have no receipt. Optional job-permission evidence stays optional.
INV-022/ADR156 and the existing full-byte configuration-base contract are unchanged;
no new decision, runtime dependency, right or format is introduced. Cheap checks
pass221 human documents/29 helpers,9 plan tests and diff check. These three public
guide edits follow gate3; a fresh required full gate is needed before commit.

Earlier live configuration checkpoint: UI3b was running as original host
session5249, new work `/home/webfixture/web022-native10-config-tags-ui3b` and
container `hfcache-web022-native10-config-tags-ui3b`. Do not rerun its launcher
or any accepted Apply. Its first Chromium/root cell passes: original previews
93c5ff1f/ff6ee7bc, original A Apply `2e0d16f357d8e2f78d41471e59c816c6`
is succeeded/confirmed/pendingfalse. The unique tag
`web022-72-chromium-root-6c4e6020` is installed; B's independently prepared
stale Apply returns409, keyed lookup404/HFAPI013 and explicit UI Compare shows
changed base, retained original draft/base and retired Apply readiness.
Missing history alone is not treated as proof of nonexecution. Operational
fingerprint02f18a10 stays unchanged while full-byte base changes b070b675→b3d7f921.
Archive exact refs/manifests and all other editable fields remain unchanged in
this first cell. Later cells and final root semantic/SDK/Stop preservation
comparison are running, so no six-cell or final wrapper pass is claimed yet.
The source3b fingerprint correction is ignored test code only; no product change.

2026-10-30 latest actual UI checkpoint: `native10-library-verification-ui2b.json`
passes wrapper0/browser0 on native72 in all three engines at both aliases. Each
cell passes twelve Library filter/restore observations, both exact publication
Files/hash/provenance views and reload/back/forward, keyboard Skip/Operations
Enter, the2/2/2/70B estimate, one original full verification POST, clean receipt/
result/persisted report and reload/Observe recovery of the same original handle
without resubmission. Root-prefix contexts first recover actual saved Stop e212
through its GET-only host-outcome UI to confirmed/pendingNo; independent job
permission reading shows Archive Allowed. Original SDK pending/Stop/API/browser
records stay unchanged. Six operation/run joins are retained in the report;
first3013046f/run358fb0bd, final8e9f2293/run89a831dd. All reports are clean,
2repos/2revs/2objects/70B, exit0, with no page errors or5xx. Chromium/root also
passes eighteen actual Library refreshes during live client integration.

`native10-cli-mcp-fresh2-result1.json` and positive-summary1 exit0: four actual
reader/writer CLI status commands across both aliases and all14 read-only MCP
tools at each alias pass, including both positive verification report reads
joined to that exact UI run358fb0bd. Original live browser init7869/start779445
and an actual Chromium descendant remain identical before/after; both observations
fall within the UI refresh window. Four app roles and SDK pending/original two
receipts stay unchanged. This is source72/native coverage; the full85×18 matrix
and rootless acceptance remain open.

Tag-only configuration UI3 exits1 before any POST: its cross-check incorrectly
expects a non-null operational fingerprint on the pure ConfigRead response.
The configuration projection loads normally; that response's outer fingerprint
is correctly null. Root semantic comparison proves no tags or other fields
changed, and original SDK/Stop/browser records remain unchanged. Failed work/
container stay retained. Fresh UI3b will obtain the operational fingerprint from
the actual status endpoint and continue the same UI Apply/stale-base workflow;
no source, permission or configuration change bypasses this check.

2026-10-30 current installed UI checkpoint: clean native source10/version0.2.72
is installed in disjoint fixture2 (boot9b4dcb96/archive3f2a1c88), with trusted
TLS and SELinux enforcing. Actual Chromium/root UI Stop passes0 as original
operation `e21207d1edea8f174cac9fe740fb09f1`: confirmed, pendingfalse and
exit_confirmed. Original SDK4563 exits normally20 without restart. Root then
reviews the original holder4559 and sends exactly one normal SIGUSR1 release;
holder exits0 and the same backend `11ae98fc8c29b085503be504e43b4139` succeeds0,
run `a9468b6cbf004e808da9990531c22473`, with two disabled repository rows and
all totals0. SDK pending bytes/inode and all original Stop/browser records stay
unchanged. Never restart that SDK, replay Stop or clear the SDK pending file.
The browser/release receipts are `native10-observer-chromium-root1.json` and
`native10-observer-chromium-root1-normal-release1.json` under
`.scratch/web-022-fresh-fixture2/`; the actual screenshot is
`chromium-root-observer-stop.png`. This qualifies one selected native cell only.

The actual screenshot also shows a host-status unavailable observation. A
subsequent trusted read in `native10-post-stop-host-status1.json` returns200/
supported with all six permissions granted. UI refresh recovery and the completed
backend result view remain to be checked directly, without a new mutation.
Current helper3790/worker4435/API4438/Caddy3826 stay active; calendars and guard
are inactive, global27:1722 is free. Initial stock-stage collector1's wrong asset
path and API/worker pre-exec203 failures remain retained. Read-only stage
postproof0 qualifies successful canonical verify/install; correcting only the
new prefix's accidental0700 mode to documented0755 allows normal startup2,
without changed source, labels, policy or hardening. These failures are not
rewritten as passes. Old source9 interrupted Stop and Firefox schedule unknowns
remain preserved in their original fixtures. Required85-case/18-cell acceptance
remains incomplete. User steering keeps execution focused on actual installed UI
workflows; no new driver, mapping or harness features are selected.

Actual read-only UI continuation1 now passes wrapper0/browser0 in
`native10-readonly-ui1.json`: Chromium156.0.8078.4, Firefox157.0 and WebKit27.2
at both root and `/management`. Each cell clicks Refresh host status and sees
supported/native0.2.72/all six permissions Allowed, then opens Operations history,
inspects exact backend11ae98fc and reads its persisted domain report. Both result
views join archive3f2/run a9468b6c and show two disabled repository rows/all six
byte totals0, success/exit0 and no report errors/warnings. All six cells have no
page errors, non-GET requests, cross-origin requests or5xx responses; contexts
and browsers close normally. Original SDK pending and original Stop/browser
private records stay byte/metadata identical. Two actual Chromium screenshots
are copied as `native10-readonly-ui1-chromium-root-{administration,completed-backend}.png`.
This proves explicit UI refresh recovery and these result views on native72;
it does not prove automatic refresh, all Administration controls, rootless or the
complete85×18 matrix. Original failed observations remain retained.

UI continuation2 (`native10-library-verification-ui2.json`) exits1 before any
POST: actual Chromium/root passes twelve Library filter/restore observations,
both exact publication Files/hash/provenance views and reload/back/forward,
keyboard Skip/Operations Enter and the read-only2repos/2revs/2objects/70B estimate.
The script omits fresh authenticated recovery of the restored original Stop
handle and the normal Read job permission evidence step. The session's restored
record guard keeps Submit job disabled until fresh per-record proof; its click
reaches30s. No original request,
key, verification admission or CLI/MCP integration starts. Browser/context close
and original SDK pending/Stop/browser records remain unchanged; failed work and
container are retained. A separate fresh browser continuation will perform that
explicit UI permission read before submission, without force-clicking or a
source/permission change. This is partial UI evidence, not a full verification
pass or a rewritten successful wrapper.

Successful gate3/focused2/3 generated test temporaries retire with retained
inventories and failed temp1 untouched. Six completed native TARs and five
successful inactive auxiliary build environments preserve bytes/metadata and
original-path symlinks in `/var/tmp/web022-retained-native-tars1/result.json`
and `/var/tmp/web022-retained-build-envs1/result.json`. The latter frees only
21,463,040 measured home bytes because logical allocation is shared; it does
not satisfy the unchanged1,062,260,736-byte browser-launch reserve. No VM disk,
operation state, failed evidence or product runtime is removed.

Subsequent completed-output preservation2 exits0: ten ordinary public build TARs
and clean-release8/9/10 trees retain all bytes/modes/owner/group/mtime/xattrs/
symlink targets and original-path symlinks, with fresh privileged zero-reference
checks. Exact success receipts and exclusive allocation are in
`exclusive-artifact-relocation-candidates1.json`; final preservation is
`/var/tmp/web022-retained-completed-artifacts2/result.json`. Actual home space
changes409202688→1094668288B, passing the unchanged browser reserve; root changes
882151424→194007040B. No guest, VM image, failed evidence or operation changes.

2026-10-30 latest checkpoint: fresh native Firefox `/management` and WebKit27.2
at root and `/management` each pass replace/resume/pause/reset with four original
confirmed/pendingfalse outcomes, one POST per keyed effect and no page errors,
failed responses or violations. Their three independent fixed-file/history/
manager probes exit0. The union with original-VM Chromium at both aliases and
Firefox at root gives qualified six-cell native schedule evidence; no successful
aggregate is rewritten and originalf041 remains pending/effect_unconfirmed in
its preserved old fixture. The fresh reports are
`native9-schedule-firefox-management1.json` and
`native9-schedule-webkit-{root,management}1.json`, with corresponding
`-independent.json` files under `.scratch/web-022-fresh-fixture1/`.

Both successful WebKit browser containers retire normally0 with historical CID
inodes and all private work retained. Firefox's normal container rm exits0, but
its first retirement collector exits1 because Podman removes the CID file;
separate confirmation2 exits0 and qualifies only that expected delta, with all
other private/report data unchanged. The original collector exit1 remains.
Normal browser removal frees guest space but does not return host qcow2
allocation. Owned guest root fstrim0 preserves the sentinel and likewise shows
no measured host reclaim.

Host retention executes the reviewed four-tree relocation and six-context
reflink-clone/reconciliation, retaining full inventories, bytes/metadata and
original-path symlinks in `retained-build-trees1/relocation.json` and
`retained-build-contexts2/relocation.json`. The six copy-on-write home copies cost
40,083,456 bytes of measured home space and release836,112,384 bytes on root;
the template stays unchanged. No live image, VM/base, operation state or failed
evidence is deleted.

`native9-drain-rw1.json` exits0: original helper4286/worker4316/API4329/Caddy4342
and guard3255 stop normally with original PIDs gone, empty cgroups and refused
Unix listeners. Root holds original device27/inode1712 through only the owned
loopback export/remount to RW, then closes that FD. Sentinel, key/configuration
guard and all12 fresh confirmed host records/original browser handles join
unchanged. No forced drain, target stop, pending cleanup or completion inference
from marker absence occurs. `native9-restart-rw1.json` exits0 with new original
tuples helper18088/worker18120/API18139/Caddy18149 under the same source9/index;
at that restart checkpoint guard and both calendars/scheduled clients are
inactive, and no SDK or archive job is started by those prerequisite steps.

The first rich Chromium/root run (original session50126) completes with wrapper1/
browser1 in `native9-rich-chromium-root1.json`; its retained progress/report
summary is `native9-rich-chromium-root1-progress1.json`. The first four blocks
pass: owned prerequisites, original recovery, explicit technical capture and
card DOM/pinned-file checks. Exactly three original POSTs succeed: recovery plan
`eb8a92b97d7df247b806dc94684e7085`, RecoveryApply
`9f1983eb0df9e95e006e7ec1d589997d` (domain run
`cc03b9cde03240349788180cea470f32`) and catalog refresh
`7bcb90541c52c638a1bd0c6a5ab4badc`. Recovery57ccd applies1/blocks0; current:f
technical/card capture and rendered/file checks pass, while old:b stays
uncaptured. The fifth block, `rich-library-typed-scope-filters`, fails at the
generic current filtered Library page deadline. No page errors,5xx or unexpected
mutation routes are reported. No quarantine/prune/purge is submitted. The failed
container/work and all original private handles remain retained, without retry
or cleanup. This is partial single-cell evidence; remaining rich/maintenance/
observer acceptance stays open.

`native9-full-verification1.json` exits0/browser0, with the complete actual public
report in `native9-full-verification1-progress2.json`. All six native engine/
alias cells submit exactly one original verification POST, no estimate request,
and join succeeded receipt, result and persisted clean full report:
3repositories/7revisions/12unique objects/23825bytes. Original operation IDs are
Chromium root`74da76342094fda378da49919b6b20f7` and
management`cf83ed4e07f5dc6fe5ad946f9c78ade0`, Firefox
root`12b34a1c706f64ebc8bd69a496db1992` and
management`82d82e0081f14ec5a6d51d51012d8179`, WebKit
root`6686854834c914bd194f44a71f41ed31` and
management`d5d7e7fce427d20873f4d79414ef914a`. Private original handles precede
terminal observation and remain retained. The earlier local mistyped-script-hash
preflight refusal has zero guest calls/browser launches/effects and is preserved
separately; it is not an unsuccessful installed verification execution.

Read-only source/API Library diagnosis finds the original collector counted all
four internal repository links instead of three canonical table rows, and its
later assertion incorrectly required incomplete coverage for a scope containing
one publication with one usable observation. Eight actual query counts are
3/1/2/2/0/1/0/1, all HTTP200/Envelope0; filtered technical
`coverage.incomplete` is correctly false.
`native9-library-filter-diagnostic2-active-before-clients.json` then
records all nine corrected browser filter steps passing, actual4links/3rows,
zero unsafe requests/page errors and an active finite refresh loop. This proves
the collector mismatch without an application fix or rewriting the original
failed rich run. The later
`native9-library-filter-diagnostic2-progress-after-clients1.json` records all21
steps passing (nine filters plus twelve refreshes), zero page errors/unsafe
requests and loop completion1793335423.980. The original wrapper nevertheless
remains running in its final wait for eight passive GET200 response observations;
private context retention/browser closure has not been reached. Original Node20725,
browser CID5689b7e4/PID20723 and session64578 are preserved without force or cleanup.
No diagnostic wrapper pass, exit0 or drain is inferred from passed assertions.

Fresh CLI/MCP compatibility exits0 in `native9-cli-mcp-fresh1.json`, with the
actual public joins in `native9-cli-mcp-fresh1-positive-summary.json`. Four
original CLI status commands (reader/writer at both aliases) exit0. All14 MCP
tools succeed at both aliases, including `get_run_report` and
`get_verification_report` joining actual clean run
`a2bbd2ee7deb400aa2676d6fc414e098`, scope3/7/12/23825. Missing credentials and
MCP credentials on the REST interface return401; correct REST reader/writer
return200. The same browser CID5689b7e4/PID20723 is independently observed before
and after clients at1793335363.282–1793335387.341, inside its actual Library
refresh window beginning1793335352.883. Source9 role tuples remain unchanged,
with no REST effect jobs or credential payload copies. This MCP client success
does not start or prove the separate scheduled SDK observer workflow.

`native9-observer-staging-recovery-preflight1.json` exits0 for staging plus
read-only original RecoveryApply/report/transaction57ccd proof. At that staging
checkpoint SDK and lock holder are unstarted. Later observer attempt1 exits1
before SDK admission in `native9-observer-chromium-root1.json`: its fixture holder
fails226/NAMESPACE before exec while masking the protected key leaf. Read-only
`native9-observer-chromium-root1-holder-diagnostic1.json` exits0 and retains
invocation`06b295194c6a4ea1a6a74c789ffd4a22`, MainPID/ControlPID0, empty cgroup,
no original1712 flock, SDK directory empty and only before/start-intent work files.
No SDK/backend POST/browser starts in attempt1. Failed unit/script/work remain
retained. Later `native9-observer-chromium-root2.json` exits1 after the stronger
whole-directory mask succeeds, without weakening stock units or policy. Its
at that checkpoint original holder22467/
invocation`d842ee9281a0463c9370840a90098dec` is active and
holds FLOCK device27/inode1712 without expiry. Stock scheduled SDK22471/
start1449514/invocation`e46f4d04693e4b0f991b2df430ff1b98` starts exactly once,
activating in `hfcache_sync_observer_t` with caps0/NNP1, and admits original backend
`f2c1b6d025e87ddd5a48e2d1c93971e1` as rest-writer in waiting_lock. Pending
inode44752599 contains288 bytes and its original key digest matches that receipt.
The collector fails before any browser/Stop on an incorrect UID983 credential
owner assertion. Actual read-only credential metadata2/ACL2 proofs exit0:
systemd257 delivers root:root0440 with exact named UID983 read ACL, parent0550
with UID983 read/execute, and read-only/nosuid/nodev/noexec credential mount
device85. Existing `credential_sources._systemd_user_acl` supports that delivery;
no application or permission fix is needed. Earlier metadata1 missing-command and
ACL1 missing-getfacl collectors remain retained. Original holder/SDK/private work/
config/pending/backend remain owned: never restart SDK, clear pending or release
holder automatically. No browser or Stop POST runs in that original attempt2.

Same-cell resume1 (source SHA2563a7d8f4813466e8faba4a7ab0051d55c139ff6c3d929ddfd508f3b4732672637)
adopts those originals without any holder/SDK start or new backend Sync admission,
then exits1 in `native9-observer-chromium-root2-resume1.json`. It submits exactly
one original UI Stop POST`eb1e5ea8ac953fe37e685985f319dc25`, expecting original
SDK22471/start1449514/invocatione46f4d04; its private original key remains retained.
Read-only `native9-observer-chromium-root2-original-stop-observation1.json` exits0:
receipt interrupted, created05:34:31.457326Z/completed05:34:45.875450Z,
domain run`80d80d6e81e346168b968afc7f3f3ddd`, result_recordedfalse; result GET is
409/HFAPI015, while original keyed outcome GET200 is effect_unconfirmed/
pendingtrue/stop_stateacknowledged. SDK exits normally20 with MainPID/ControlPID0,
empty cgroup and failed unit state, retaining original invocatione46f4d04.
At that resumed failure checkpoint holder22467/invocationd842ee92 stays active/
FLOCK27:1712 without expiry or
release, and backendf2c1 remains waiting_lock. Browser closes normally after its
120s DOM deadline, with zero page errors/violations. Both original host Stop
pending and SDK pending inode44752599/288bytes, keys, configuration and all work
remain preserved. Never retry Stop, restart SDK, reset/clear pending or release
holder automatically. Actual helper timing2 later identifies the post-exit
`host_policy.validate` line1757 mount-row comparison, rather than a slow read in
this case. A public dummy-credential probe below confirms the exact lifecycle
without hardening relaxation; the implementation and validation checkpoint below
records the subsequent fix.

Root explicitly releases the original owned test holder once by SIGUSR1 after
source/normal SDK exit20/original keyed Stop uncertainty/quiescent-helper proof.
This diagnostic action does not reconcile the Stop. Executed release script
SHA25642382ca0c858dca9d308e207794d1a6c42c823351d0b1ee7d80bb5218a21cb5f
retains the unexecuted ee5aa574 draft; only port8443→22443 differs. Stage exits0.
`native9-observer2-diagnostic-holder-release1.json` exits1 only after the explicit
release, backend success0 and report validation, at its incorrect
`report.repositories == []` assertion. Independent read-only
`native9-observer2-post-holder-release-readonly1.json` exits0: original holder22467
is gone/MainPID0/empty cgroup/normalExit0, unit active/exited with invocationd842ee92;
original SDK22471 is gone/MainPID0/empty cgroup/normalExit20, failed unit with
invocatione46f4d04. No device27/inode1712 flock remains. Original backendf2c1
succeeds0/run`827145e7caa04cdbb44f172256fc1e48`; its persisted SyncReport has two
configured disabled repository rows, every total0 and no errors/warnings.
All original SDK/host pending, Stop receipt/ledger and browser/original-work
snapshots retain exact metadata/hashes. Stop eb1e remains interrupted/HFAPI015/
effect_unconfirmed/pendingtrue/acknowledged. No new Stop, SDK start, pending clear
or Stop reconciliation occurs, and observer acceptance is not passed. The four
source9 application roles continue under owned NFS-RW with guard inactive.

A separate public-only credential-mount probe is initially a retained live owner, not
the SDK or archive-lock holder. `native9-public-credential-mount-probe1.json`
exits1 at metadata assertion181 before its signal: systemctl displays complex
credential properties as `[unprintable]`, even when empty. Original unit
`hfcache-web022-public-credential-mount-probe1.service` remains active with
PID23895/start1794978/invocation`600413cd91ef47d69336864e8ce10d76`, no expiry and
no archive flock. It runs hardened UID983/caps0/NNP1/no-IP, with the real archive,
credentials and API/helper endpoints masked; SetCredential contains only the
known public dummy. Typed `native9-public-credential-mount-probe1-typed-properties2.json`
exits0: LoadCredential and LoadCredentialEncrypted each have typed a(ss) zero
entries, ImportCredential typed as zero entries, proving zero real credential
source references. The earlier typed1 false-shape collector remains retained.
Exactly one global credential mount is observed at `/run/credentials/` plus the
fixed probe unit, tmpfs device72/mount ID891, RO/nosuid/nodev/noexec/nosymfollow/
noswap. Original before/raw/effective/failure evidence remains retained.
Subsequent continuation stage0 and
`native9-public-credential-mount-probe1-continuation1.json` exit0 without any new
start: one explicit SIGUSR1, original retained pidfd exit observed and normal
service exit0. Full sanitized
`native9-public-credential-mount-probe1-continuation1-result-readonly.json` exits0:
exactly that one credential mount disappears, no mount is added, ordered prior
projection is restored and original/unknown records stay unchanged. Original
probe23895 is inactive; final manager state is not-found/inactive/dead with PID0/
empty cgroup. The original systemd-run waiter PID23893 is currently absent, but
its start identity/reap/exit were not captured; no waiter exit0 is claimed.

This confirmed probe authorizes the contract-first narrow amendment: dated
ADR156 amendment/ADR150 cross-reference, host-administration/security/INV022 and
ADR index permit only an exact captured fixed SDK credential mount's removal
after the trusted original-stop flow proves retained-pidfd exit. Unchanged
projection still requires identical raw credential-mount identity; original
capture, all unrelated mount observations, protected authority and budgets remain
strict. No new model/protocol, right, generic refresh or path-prefix exclusion
is added. The subsequent narrow implementation captures the single stock-shaped
mount's raw identity and permits its exact removal only at the observer clone's
actual final validation read, preserving strict original/default validation.
Focused host-policy/action regressions pass293 tests/26.10s, Ruff/format and focused
Pyrefly pass; `observer-credential-mount-focused1.json` retains exact source hashes
and earlier failed/corrected runs. The final timing regression covers teardown
between confirmation setup and final validation. Failed temp1 and successful
temp2/temp3 remain retained at this checkpoint. No runtime timeout, transport,
privilege or protocol change is added.

Required repository gate3 passes0 in1580.36s with
`scripts/check.sh --require-web --require-cockpit --with-build`:9481 backend/
52 opt-in deselections,3708 web unit/4049 combined frontend and16 wheel smoke
tests; all1006 frozen product files stay unchanged. Log SHA256
`6ec63159adccba3817d45450a05086f205483cd287a8cfcc4b9bc732e4fa13a9`;
`gate3-start.json`/`gate3-result.json` retain exact execution. Cheap prechecks
pass221 human documents/29 helpers,9 plan tests and diff check.

Clean detached source10`54e86929c30321a2f4efc9df42fee4b46f9e117a`, test-only
version0.2.72, builds0 in17.27s with reproduced backend/UI bytes. Snapshot
`a42f125d946b9f5833610c2d182525b42d2e4de1f9ae1dc247c98f85682e5c0a`, native index
`6e987d4c326503325fa425e50898d396b28eff891c6ef803679dca19fb2d3dd7`, UI manifest
`b26d4419e679f2e4287c9a4ad5186aa7b692bbe3d8f5699afc2b46ae5e9e825b`.
Main branch/index/version0.2.2 remain unchanged. `clean-source10.json`,
`build10-exit.json`, indexed build evidence and `native-release10-pack.json`
retain exact provenance; no API-container build or installed acceptance follows
from this native input build.

Separate fixture2 launches0 from the immutable backup into a new home-volume
overlay: QEMU1108191/start22697517, boot`9b4dcb96-6fdc-4d56-bc65-49f4aee47278`,
DMI`01bba4d6-f334-458b-891a-37ec4fc27022`, restricted loopback SSH46323 only.
The first launch preflight1 refuses on a protected process FD before disk/QEMU
creation; corrected privileged read-only FD inspection precedes actual launch2.
The first SSH observation255 is pre-banner during boot; readonly observation2
and initial inventory1 pass0 with SELinux enforcing, no application actors,
all system roles/guard inactive, writers/calendars masked, no archive mount,
copied key61259513/config guard61244163 unchanged and absent first boot-local
global lock. Original fixtures stay preserved. Fresh native installation,
positive observer control and the full85×18 matrix remain open;
original interrupted Stop eb1e and both pending handles are unchanged.

Remaining-maintenance stage0 in
`native9-rich-maintenance-chromium-root1-stage.json` creates only nine pinned
public files in a fresh work path, with no POST during staging. Its continuation
completes wrapper1/browser1 in `native9-rich-maintenance-chromium-root1.json`.
The actual `-report.json` retains passed original-read preflight/quarantine
blocks, four original succeeded POSTs and no page errors/5xx/violations:
quarantine plan`cf4adbe0efb58ea45472309b383e87f9`, cleanup
`45733bcdfcda55137d0bcb9dd6397412`/run`61f7780d2aea4ba98eeae96ab6420c7b`,
prune plan`7a002211745b4920a59ccf738bea16b8` and prune
`9a6e2e2f93ee8c4aac37e6d8ef8724b4`/run`7a78725ccee8448b853c8276a8330d2c`.
Cleanup removes one4288-byte file. Prune applies:b, removes two files/4751bytes,
retains c/d/e/f and preserves current:f; the prune block then fails only its
final legacy-reference assertion409!==404. The wrapper/block failure and all
original private handles remain unchanged; no completed mutation is repeated.

`native9-maintenance-post-prune-readonly1.json` exits0: legacy reference:b is
409/HFVER008, exact:b/b card and catalog membership are404/HFAPI007, and current:f
is200 with its original pair. Both original cleanup/prune receipts are succeeded/
result_recorded with Envelope0. The separate mistyped `/api/v1/revisions` GET404
is only a diagnostic wrong-route request, not inventory proof. A future ignored
candidate3 corrects endpoint assertions and passes Node syntax only; it is not
executed and does not rewrite the failed attempt or change application code.
Purge-only stage0 retains nine pinned public inputs. Its fresh session25875 then
completes wrapper0/browser0 in `native9-rich-purge-chromium-root1.json`, with
both read-only preflight and existing purge block passing. Exactly two original
POSTs are retained before terminal observation: plan
`77b6ff5cb087a6977017faa145e9640e`/run`5b164cc440c145a8a0ec3236fe9a9366`
and Apply`cf2c36ef4f732a8be7559101608a8d18`/run
`b6b96430e71142ae9d2ca8950629a3c0`. Current card is deeply equal before/after
purge; context/browser close normally with zero errors/5xx/violations. Original
recovery/capture/cleanup/prune are never replayed, and the failed maintenance
wrapper remains1.

`native9-post-maintenance-independent1.json` exits0: typed repositories contain
two managed disabled entries (model current:f/retained4, dataset current:15/
retained1), and `/repositories/revisions` returns five revisions marked verified.
The read-only estimate is2repos/5revs/9objects/19039bytes/unreadable0, not a new
full verification. Both unexplained staging/quarantine sibling files retain
exact metadata and hashes against the original before snapshot. The six earlier
full verification reports keep their pre-prune3/7/12/23825 scope. Observer2 SDK
exits20 and its original backend succeeds0 after the explicit diagnostic holder
release; Stop remains unconfirmed with both pending handles preserved. Observer
acceptance and complete profile/cell acceptance stay open.

Two completed old source TARs are preserved under
`retained-build-archives3/relocation.json`, execution0 with bytes/modes/owner/
mtime/xattrs/original-path symlinks retained and zero privileged proc references
or unreadable observations. Root space changes978206720→1044688896 bytes; final
home space752717824→686149632 bytes. The executed script SHA25681e8aeb5 retains
the original99e41361 draft; its only adjustment isolates the privileged read-only
proc child with `-I -B`. Successful524-test pytest3535 retirement then exits0 in
`selected-engine-524-successful-temp-retirement-result1.json`, measured root gain
41197568 bytes, with every other temp directory, pytest-current alias and audit
unchanged. Successful522-test pytest3534 retirement also exits0 in
`selected-engine-522-successful-temp3534-retirement-result1.json`, measured root
gain41652224 bytes, with other directories/pytest-current/audits unchanged. Its
first creator-argv self-reference refusal remains retained; fresh privileged
read-only proof2 has zero references/unreadables. The source test's original OS
PID was not captured; its tool session is not substituted for one. No failed/
unknown state, VM/base/image or operation evidence is deleted.

Two additional positively verified successful contexts are retained in
`retained-build-contexts4/relocation.json`, execution0, bringing the preserved
build-tree/context total to12. Source3 native inode162399592 and source4 rootless
inode19815623 retain full bytes/mode/UID/GID/mtime/xattrs/symlink/nlink inventories
and original-path symlinks after template reflink/reconciliation; template stays
unchanged. Executed script SHA256ad63f6ff3949ef0c652787153479fcfbdb0689a493295d12fca097122e48ebfe
uses the privileged read-only reference checker before each mutation, with zero
references/unreadables. Root availability1010364416→1287606272 bytes and final
home682856448→668286976 bytes qualify this resource checkpoint only. No image,
VM, operation or failed evidence changes, and existing resource guards stay fixed.

Internal selected-engine fixture support changes only four test-tool files;
default all-three engines, public CLI/manifest, eleven mappings and strict85×18
requirements remain unchanged. A selected-engine run refuses final/through-task
aggregate claims. Focused `pytest tests/unit/test_web_functional.py -q` passes524
(36.40s; actual tool session20465/chunk8c0cd6), and Node driver tests pass15
(session32199/chunkab1561); Ruff/format/ESLint/Prettier/Pyrefly pass. These receipts
are actual tool transcripts, not invented log files. Gate2 is prior-green evidence
for its frozen snapshot; a fresh required full gate is pending for these tool
changes. Packaged source9 runtime/artifacts remain unchanged and their installed
checks retain their exact scope.

A subsequent partial AUTH02 test-tool step remains confined to those four files:
23 baseline IDs include `denied-basic-read-auth`, with13 GET-only raw/wrong/
malformed Basic probes requiring exact401/HFAPI001. AUTH02 stays unmapped; default
CLI/engine selection and strict85×18 requirements do not change. Focused Python
checks pass45/498deselected in5.49s (session48155/chunk3e5191), existing TLS auth
checks pass9/61deselected in7.94s (session57987/chunk97c283), and Node checks pass17
(session73736/chunk0807e2). Format/lint/full Pyrefly also pass0, last Pyrefly
session57816/chunk50ba3f. These are actual tool transcripts without standalone
original logs; no installed/guest or runtime/dependency changes are credited, and
the full required gate remains future. The full85-case/18-cell matrix remains substantially
incomplete; eleven implemented runner case mappings cannot stand in for it.
WEB-022 remains in_progress, with all production/source/retirement holds intact.

2026-10-29 checkpoint: required gate2 exits0 in2043.63s with all1006
frozen product files unchanged:9402 backend passes/52 opt-in deselections,
3708 web unit/4049 combined frontend and16 wheel smoke checks, including the
required web/Cockpit/build checks. The retained log is
`.scratch/web-022-validation/gate2.log`, SHA256
`99afc00c1674516eeb8ee819c376866b235a79109b98bb72ae39cfd4ef215712`.
This repository gate does not complete the installed85-case/18-cell matrix.

Three source9 native schedule cells pass their four original UI effects without
retry: Chromium at both aliases and Firefox at root. Firefox `/management`
replacement`f04156226b4e9fa82b4268e59102c0f6` remains interrupted, result409/
HFAPI015, with its original protected outcome effect_unconfirmed/pendingtrue,
file installed and manager unknown. The exact original key, pending state,
fixture and failed browser report are retained; no replay, reset or success
relabel occurs. `native9-preservation-drain1.json` exits0: original API/worker/
helper/Caddy stop normally, their original PIDs disappear, cgroups empty and
Unix listeners refuse connections. That original guest remains guard-only on
bootb2f9c836, NFS-ro, with READYguard25331 holding original global1641.

A separate owned target is prepared from the retained pre-recovery backup,
boot`a213b3ea-5945-4a1d-ad4d-8cf354393a36`,
DMI`e3fd4f91-5ac8-4cb0-9157-d665ea0f9930`, archive
`8ac4089b-1960-429e-b67c-04c6fbd45cbb`. Its
`.scratch/web-022-fresh-fixture1/ro-storage-provision2.json` exits0 and records
loopback-only NFS-ro, READYguard2511/invocationc23fa8129e9241ca84a6769ce7205ec0
holding device27/inode1712 and no application service starts. The first storage
attempt and initial refused ownership collector remain retained. Fresh cold
preparation preserves the copied predecessors and creates separate API/worker
stores with zero enabled repositories. Subsequent canonical native selection0
in `native9-selection1.json` selects0.2.71, retains original1712 and normally
hands off guard2511 to READYguard3255/invocationee54e2dfbede4307a1e30d15710513fc.
All nine unit labels are verified, including dedicated sync timer85965898;
that selection record confirms empty fresh stores and stopped application
services. The separate
protected server refresh0 changes only the indexed web asset root/hash while
retaining the predecessor. `native9-v2-provision1.json` exits0/provisionedtrue,
publishing the canonical20-role receipt
`fe1240656f093e13d4f9563fad36b1c007c3052e047e2af94ccacc50faa573e6`
with guard3255 retained and zero service starts. It preserves the original
history/SDK/key/configuration guard/receipt and loaded CIL/kernel identities;
canonical persistent rules respect the measured systemd-path equivalency.

Owned HTTPS fixture setup2 exits0: private source coherence and trusted TLS
metadata GET pass, with the isolated nobody service at127.0.0.1:25444. Only
`hub.endpoint` changes in application configuration, to that HTTPS address;
the original config is retained. The initial source-check permission refusal
and its logs remain preserved. This is fixture setup, not an application repair.
Manager DefaultEnvironment supplies the public CA bundle; the API's selected
`SSL_CERT_FILE=/etc/pki/hfcache-web022-owned-ca-bundle.pem` is independently
observed without logging other environment values.

Publisher1 refuses before effects because its collector incorrectly requires
an empty helper drop-in list. Numbered publisher2 accepts only the exact retained
stronger fixture mask, publishes the reviewed native bindings, then retains
the actual pre-exec233/RUNTIME_DIRECTORY helper failure. The documented cold-
boot runtime parent/API directory provisioning0 supplies only their required
ownership/modes/labels; policy, deployment, original guard and failed invocation
remain unchanged. `native9-start-continuation3.json` exits0 without republishing:
helper4286 runs in the native helper SID with caps0xc0; worker4316/API4329 are
UID983/caps0 and Caddy4342 is UID982/caps0. All four have NNP1/seccomp2 and
the expected original process/cgroup identities. API/worker drop-ins remain
empty; the stronger helper and historical Caddy fixture masks remain intact.

`native9-tls-readiness1.json` exits0 with verified private-CA TLS: bootstrap,
status and host status return200 at root and `/management`; status/host-status
Envelopes exit0. Source9d687e67, UI69a9b2a1 and archive8ac4089b join the published
deploymentdd557dd1/policyc7fb5a21. Host state is guarded: archivefalse/guard-held,
the other five grants true. The intentionally retained fixture warnings remain.
Guard3255 still holds original device27/inode1712 on loopback NFS-ro, both
calendars stay inactive, and no fresh browser or positive workflow is claimed.

Only completed successful gate2 pytest temporary files are retired after exact
owner/process/mount checks (`gate2-successful-temp-retirement-result1.json`);
the gate log/hash/source/artifact records and failed temporary state remain.
No build tree is relocated or deleted. `browser-vfs-capacity2.json` records the
actual2.55GB image and one shared Chromium extent in an existing stopped layer;
aggregate capacity preflight remains open before a new browser launch.
The earlier checkpoints below
retain their original source/boot scope and do not describe current live actors.
WEB-022 remains in_progress; observer, maintenance/card/capture and complete
native/rootless installed acceptance remain open.

2026-10-29 continued source9 checkpoint: the original auth/navigation run retains
its wrapper600-second timeout and independently observed original container
exit1/PID0. Its real report contains passing Chromium/Firefox at both aliases
and WebKit at `/management`, with zero page errors, plus a WebKit root immediate
fragment-URL assertion failure. A fresh root-only WebKit execution waits for the
Files tab and then checks exact URL/publication identity; it exits0 with all
remaining auth/header/native Stay/Leave/history assertions and no page errors.
This is a qualified union of five original passing cells and one targeted cell,
not a rewritten successful aggregate. History restoration succeeds; BFCache
was not observed and is not claimed. Original reports, container identity and
failed assertions remain under `.scratch/web-022-validation/`.

The first native schedule browser cell submits no POST: original UI reads
produce typed helper-unavailable evidence and keep the action disabled.
The read-only diagnostic records that UI state and its actual request timings;
later independent status/observer reads succeed with matching bindings and
grants. No permission, deadline or source change is made to bypass the refusal.
Subsequent single-flow results are recorded in the latest checkpoint above;
this original no-POST refusal remains separate from those positive effects.

Required gate1 exits1 after9400 backend passes/52 opt-in deselections/1433.59s,
solely because CLI help exposed an implementation identifier. All1006 frozen
product files remain unchanged; log SHA23411d71 is retained. The help uses a
public task placeholder now. A separate fresh-fixture coherence defect is also
fixed before initial serialization: rich entries derive their Git blob OID from
the actual bytes instead of inheriting an example placeholder. Both older
fixtures remain unchanged; a new UUID fixture has twelve independently checked
Git OIDs and clean full verification-engine results. That is host coherence,
not installed repair/NFS acceptance. Focused fixture/help/plan66 tests, docs and
Ruff pass, and required gate2 subsequently passes on the new1006-file snapshot
as recorded above. Native
source9 application artifacts are unchanged by these tooling/fixture corrections.

2026-10-29 source9 installed checkpoint: canonical offline stage, actual119-module/
16-artifact/runtime audit, exact ordinary drain, RO original1641 guard handoff and
canonical0.2.71 selection all pass. Source8 remains intact with protected server/
deployment/policy originals and receipt1/history/SDK inodes retained privately.
V2 native provisioning preserves key61259513/configuration lock61244163 and
loaded CIL/kernel policy, adds only the required fixed labels/context/client
settings and records the canonical20-role receipt. The first preflight collector
misread omitted socket PID properties; a second attempt reaches the measured
CentOS systemd-path equivalency refusal. Both failures remain, and a separately
validated continuation uses the canonical persistent-label path without changing
the equivalency or rerunning filesystem provisioning. No service starts occur
during that continuation.

Canonical native helper proposal0 binds clean9d687e67/snapshot92d01ee4,
UI69a9b2a1 and receiptfe124065, including the exact observer context. Explicit
native positive-control policy is published only in the owned guest. Helper/
worker/API/Caddy now run the candidate under the RO guard, both timers inactive.
Actual steady role observations pass UID/capability/NNP/seccomp/context checks;
the first start collector's combined worker NNP/seccomp assertion failed after
start, with those initial values unretained. Its original failure remains; the
follow-up records actual process observations without restarting helper/worker.
Fresh3-engine auth/routing/native Stay/Leave/history checks are running, not yet
accepted. Required repository gate1 is running on1006 frozen product files;
the complete85-case/18-cell installed matrix remains pending. Runner case results
now derive from actual per-engine assertions; the eleven implemented mappings
cannot satisfy the strict85/95-case gates by stamping unexecuted case IDs.

2026-10-29 continued installed checkpoint: read-only confirmation of the original
reserve Apply passes with no POST or replay. The source8 services then drain
normally, with original PIDs gone, empty cgroups and refused listeners. Root
holds the same original global lock1641 during the owned loopback-only NFS
read-write transition; the sentinel, configuration lock61244163 and helper
key61259513 stay unchanged. The same pinned services restart with Enforcing
SELinux and the private worker's no-IP/no-credential confinement preserved.
Both calendars remain inactive; the read-only guard is inactive for this owned
writable phase. No production/NAS mount or service is involved.

Actual installed REST-writer `verify --full` exits0 through trusted Caddy and the
offline worker: report `4ccc68bae8fb424d9e71c4cf0f1e47c2`, two repositories,
two revisions, two objects/26 bytes, no findings or warnings. Original CLI
operation keys remain guest-private. Three earlier client-configuration/CA
access refusals happen before admission and remain retained. The three-engine
read smoke passes at root and `/management`. All fourteen MCP tools, including
both formerly absent positive report reads, and the REST credential separation
checks pass at both prefixes while the same browser container is independently
observed running before and after the calls. Evidence is in
`native-real-verification4.json`, `native-positive-browser-smoke1.json` and
`native-positive-rest-mcp1.json` under `.scratch/web-022-validation/`.

The WebKit chained-fetch experiment reproduces navigation errors only when
follow-up reads start after navigation begins; explicit read-owner cancellation
prevents them. Scoped document lifecycle and queued-read fences now accompany
the independent already-aborted promise fix. Focused400 unit/82 component tests
and type/lint/format checks pass. Clean auxiliary candidate9d687e67, fixture-only
version0.2.71, has reproducible native/rootless artifacts and successful host
image/runtime probes. It is not yet installed: fresh navigation/dirty Leave/
BFCache, native positive controls, maintenance workflows and the complete
85-case/18-cell installed acceptance remain open. No full gate or task completion
is claimed by these partial observations.

2026-10-29 installed checkpoint: actual native auth/route2 passes Chromium and
Firefox at both aliases, including deep refresh/history, exact publication,
headers, pagination, Basic/MCP separation and four denied pure-validation CSRF
requests per alias. WebKit reaches those assertions but reports navigation-
related inspector errors; both raw failed runs remain retained. Passive WebKit
diagnosis records17 automation page-error reports, zero DOM error/rejection
events and requests attempted after full navigation begins; attribution remains
open. An independent already-aborted reader promise bug is fixed with361 focused
tests and type/lint/format passing; it is not yet claimed to explain WebKit.

The real UI reserve edit100→1GiB (10% unchanged) succeeds as original Apply
`3beaf9f56ccb04fa9cc3f1a1d768502b`, preview`b755158983c6dd69855813e693ae17a2`:
receipt succeeds, result0, original keyed host outcome confirmed/no pending.
The collector remains false because its final assertion wrongly equates opaque
installed-base and candidate revisions. Original keys and both registry/storage
files are retained privately; no Apply is repeated. Independent read-only host
observation confirms1GiB/10%, new config inode61513907 and unchanged global1641/
configuration61244163/key61259513. A read-only UI confirmation is next. Initial
collector1 failed after pure validation only, with no preview/Apply. All prior
browser cohorts are independently observed stopped/PID0 with their real exit1.
Artifacts are under `.scratch/web-022-validation/`; no positive archive job,
writable transition, native v2 grant or final functional acceptance is claimed.

2026-10-29 sequencing correction: the original invocation of the final
`--with-web-functional` gate here also required RELEASE-08 (Cockpit absence,
owner WEB-025) and final handoff cases owned by WEB-026. Those packages depend
on this task, so applying their final conditions before WEB-022 would create a
dependency cycle and premature retirement. Existing ADR143/testing strategy
already separate early installed acceptance from the WEB-026 final gate.
The existing runner therefore gains a strict through-task requirement, not a
second runner: WEB-022 requires all85 cases owned through022 in all18 cells;
WEB-023/024/025 add their owned cases in order. `--final`/the final repository
flag still require all95×18 and cannot combine with a through-task selector.
No required case is cancelled, skipped as passing, or retired early. Later
completion rows and original failures remain unchanged until actually proved.

2026-10-29: dependency WEB-021 is committed as2c44f2d with final required gate0,
four completed acceptance rows and clean source245f2eaa installed artifacts.
The user's continuation goal authorizes this package without another stop.
Startup revalidation in `native8-handoff-state1.json` verifies the owned guest
bootb2f9c836/Enforcing, current API8198/worker9573/Caddy8204/helper8112/guard8071,
original global1641/configuration61244163/key61259513, loopback NFS-ro and both
inactive calendars. Root alone owns every guest/service mutation; source/fixture
preparation may proceed independently. Existing installed smoke is partial:
14 MCP tools invoked but12 positive/2 absent reports, and native grants remain
configuration-only. Full workflows, native positive controls, actual role probes
and the explicit owned functional manifest/gate are required here. Reuse valid
historical evidence only within its exact source/profile scope. Preserve all
failed/unknown evidence and original handles; no force, replay, production/NAS,
remote publication or live Cockpit removal.

## Completion evidence

2026-11-01, **WEB-022, this commit**. All85 scenarios owned through this package
are completed in the existing95-case ledger at their unchanged minimum layers;
ten later-owner scenarios remain pending. Reconciliation preserves original
executions, failed aggregates, accepted operations and explicit uncertainty.

- Installed candidate **0.2.78**, clean runtime source
  `f829857ec045ce4616055e357e7d6aa7047287ca`; UI manifest
  `57828b507735fbd4197a72d76a3a6f54752678c9eac11de22e240a7e0dda3ad9`;
  native index `a251b77e9b8f51598ca0b08314c21ef3d7f01d793fadd91265fbc1d7855be0b0`;
  rootless manifest `f8b037595efc3ec93f286f2b5bc6f741e34a756185130eb380880f06498435ed`.
  Main package metadata stays0.2.2. Actual installed roles, executable/module
  identities, sockets, cgroups, mounts, peer/secret visibility and effective
  no-IP probes are recorded separately from source-fixture simulations.
- Actual Chromium156.0.8078.4, Firefox157.0 and WebKit27.2 cover native/rootless
  root and `/management` entrypoints. Deep domain/fault evidence is reused only
  with the recorded unchanged-subsystem justification. Exact commands or retained
  entrypoints, exits, node/callback IDs, source/artifact hashes and observed scope
  are in `acceptance-evidence.json`. Unretained original inline-probe argv is
  explicitly identified; it is not reconstructed as an observed command.
- Real configuration additions/removal/stale-draft409 and original-outcome
  recovery, maintenance/Purge/Repair, native schedule/observer effects, rootless
  denials, CLI/all14MCP tools, browser/client overlap and genuine current78 worker
  report joins have actual retained proof. The unexplained Library lookup,
  Firefox response-event discrepancy and unobserved cross-origin form Basic
  attribution remain qualified. Authenticated hostile Origin/media combinations
  have actual TLS/ASGI/protocol coverage; no broader browser attribution follows.
- New actual password/hash/username rotation preserves subject, original durable
  handle and independent bearer sources. Focused provider66 tests pass0 in5.95s
  (`auth-rotation-resume1-result.json`); Ruff/format/Pyrefly pass. Successful
  read-only qualification of the already executed6×13 named Basic refusals is
  `auth-read-refusals-qualification-resume1-result.json`; original browser1 and
  unrelated workflow failure remain unchanged. No product effect is repeated.
- Required full command
  `rtk proxy scripts/check.sh --require-web --require-cockpit --with-build`
  passes0 in1744.448s (outer0/1745.113s): **9646 backend**,52 unrelated opt-in
  deselections; **4051 combined frontend** (3708 unit), **581 Cockpit** and
  **16 wheel** checks; three locked install profiles, two built-browser checks,
  real HTTP/API fixture,175 transport definitions and strict lint/types/docs.
  Frontend coverage95.02% lines/90.13% branches; static build1220003B,
  JavaScript254759gzipB. No required skip. All **1545** frozen inputs unchanged.
  Gate21 result SHA `34a768e52570b247ee37925fe5b5511bd8f2e5f40256a41b3081dc8eba1bd408`;
  log SHA `770728a62a9e56fc29783fa5d661fbb0907a9abf39491c0044716609f6bc8ce7`.
  Records live under `.scratch/web-022-validation/` as `gate21-result.json`,
  `gate21-shadow1-result.json`, `gate21.log` and
  `source-current-product-focused-acceptance-freeze13.json` (SHA
  `74e2da3217f1e90a78cf302480ad9b137ae00cc1621a87bb3e26250510a6f998`).
  Tests run as loginUID1000 with private emptyRO NAS shadow. These are source
  and disposable installed checks, not production/NAS acceptance.
- Acceptance/closure records are adopted after the frozen source gate;
  `web022-ledger-adoption-resume1.json` proves all original executions and
  minimum layers retained. The optional strict runner and its protocols are
  unchanged; no `--require-through`, `--final` or `--with-web-functional` pass
  is claimed. Missing-test list through022 is empty; the remaining10 cases
  belong to023–026 and are not passed by this package.
- Reviewed INV005/018–022 and ADR033/143/145/147/150/153/154/156; same-package
  contract amendments cover initialized layout inspection, logical published
  bytes, configuration Apply/read binding, HTTPS authority ports and accepted
  test scope. No runtime dependency or durable-format migration is introduced.
  Human deployment/configuration/navigation/Library/troubleshooting guides and
  [test-release summary](../../../web-ui/test-release-acceptance.md) align.
- Completed [progress entry](../../progress.md#web-ui-replacement-2026-10-20),
  plan/current pointers and Operator handoff advance to pending WEB-023.
  Refresh/apply every related bounded-testing and GPT-6.1-sol effort amendment
  **after this commit and before WEB-023**: high/medium/high/medium. Preserve
  production/NAS, credentials, user caches, original locks/unknown handles,
  disabled calendars, historical failures and live Cockpit. No merge/push/tag.

Post-adoption record checks: `rtk uv run --locked --extra server --extra mcp
python scripts/check-docs.py` exits0 (222 human documents/29 helpers),
`rtk uv run --locked --extra server --extra mcp pytest tests/unit/test_web_plan.py`
exits0 (9 passed/0.41s), and `rtk git diff --check` exits0. Initial record checks
refused agent IDs in the human summary and empty node lists in five new schedule
supplements; prose and actual retained workflow function identifiers are corrected.
No runtime/test/build source changed after Gate21; only the six closure/acceptance
records differ from its freeze. Original product failures remain unchanged.
