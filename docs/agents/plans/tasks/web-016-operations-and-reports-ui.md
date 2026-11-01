# WEB-016: Expose existing jobs, verification, diagnostics and reports

Interface-only instructions and source references have been omitted from this
retained shared record. Exact original text remains in Git `c692d7ae4b866fefd8a743a21afdb729da0f39c4`;
original document path SHA-256 `4174c708c5826ab8774f27106726bc7142a8beb2e16ea1138802aad61611cf7e`,
original content SHA-256 `5f4cc640c137f6937181c34f71d73bdf419a707d0a9bcea6b496b9373a4b9a71`.
Historical proof hashes identify the original artifacts, not this edited record.

| Field | Value |
| --- | --- |
| Status | completed |
| Plan | [Web UI replacement](../2026-10-20-plan-web-ui.md) |
| Phase | P3 |
| Depends on | [WEB-015](web-015-configuration-and-tag-ui.md) |
| Branch | `feat/web-ui` |
| Work-package commit | `WEB-016: expose jobs and exact operation reports` (this commit) |

## Read before implementation

Also read the relevant sections of [architecture](../support/web-ui/architecture.md), [API contracts](../support/web-ui/api-contracts.md), [testing strategy](../support/web-ui/testing-strategy.md), [acceptance matrix](../support/web-ui/acceptance-matrix.md), and [human documentation map](../support/web-ui/documentation-map.md). Load only affected living contracts and ADRs through their indexes. Refer to the [source review](../support/web-ui/source-review.md) for pinned baseline evidence; current git wins over it.

## Scope and implementation requirements

Implement Operations list/detail, original lookup, event/result presentation and run-report browsing. Connect full/selected sync, installed/candidate sizing, new/full/exact revision verification, estimate, diagnostics read-only/probing and metadata refresh to existing routes. Explain each scope's archive/Hub/control effects and effective permission. No byte percentage unless actual validated progress supplies it; no Cancel button.

Render queued/waiting-lock/running/terminal/interrupted/unknown observation separately, with persistent error/warning codes and full per-repository partial results. HFMNT010 is benign busy; integrity findings persist and direct to review/repair rather than suggesting blind sync/prune. Keep run IDs distinct from request/operation IDs. Show report and operation pagination and known loaded extent. Bounded journals are not substituted for results.

Navigation, background tabs, retries and page refresh retain original handles and do not resubmit. Expose read-only observation/export of safe original handles for operator handoff, not bearer-bearing URLs. Continue enforcing one unresolved mutation submission lane in the UI and backend guards.

## Unit and component validation

Component/state tests cover each action DTO, scope, permission, 202 versus completed output, every domain classification, partial reports, busy and missing-history results; ensure no mutation is registered as a read retry.

## Integration validation

Use real service/runner/private-worker fixtures for sync/verify/diagnose/refresh and reports with no live Hub. Inject queue wait, original-key conflict, worker disconnect, result size/event gaps and history expiration.

## Functional validation

Three engines submit/observe representative sync, verification, diagnostics and refresh via Caddy, then reconnect after dropped response with no duplicate effect. Follow a run report from repository detail and preserve findings/loaded-history labels.

## Human documentation deliverables

Complete operations.md and relevant troubleshooting/runbook links; update actual job examples and clear no-cancel/observer limitations. Human guides distinguish offline refresh, Hub sizing/diagnostics and verification.

## Acceptance

Existing operational capabilities are reachable and observable from the SPA with exact results, safe original-handle recovery, bounded reports and no fabricated progress/outcome.

Historical execution summary: the recorded gate included the retired interface; exact invocation and original proof remain in Git `c692d7ae4b866fefd8a743a21afdb729da0f39c4`.

## Execution notes and blockers

Started2026-10-26 from clean completed WEB-015 `1cc5b81`, after strict
gate3 and36 actual installed cases. Reuse the existing typed submission,
query/retention and original-operation controller; add no endpoint or runtime
dependency. Preserve OPS06–09 distinctions, request/operation/run identities,
bounded loaded histories and original-key/no-replay behavior. Source scopes
cover job forms, paged operations/reports and root composition/integration.

Application-functional tests reuse the existing guest/Caddy/browser tooling
with a fresh owned runtime/archive/API/private-worker state prefix. Only the
external Hub and explicitly labelled storage/mount-table test seam may be
deterministic, as permitted by the testing strategy; production routes/services,
real Unix worker and durable effects remain actual. This does not close later
NFS/platform holds. Preserve the completed WEB015 fixture's original pending
configuration, candidate/backup/history/API stores and lock/key; do not reuse it
for new writes or clear its state. No new guest/engine framework or production
service/NAS/credential/guard change. Feature smoke tests precede the final source
freeze/full gate so real protocol problems are found early.

Current source work connects all existing manual DTOs through the original-key
controller, bounded operations/events/results and run reports through the shared
query/retention owner, and an explicit repository Activity link to Operations.
Focused root query/workspace/repository tests44PASS; existing App/recovery15PASS;
strict TypeScript passed while feature tests continued. These are source checks,
not installed functional acceptance. A new real ASGI/runner-to-Unix-worker test
also exercises actual sync publication, new/full/exact verification and durable
report equality, integrity exit40 without healing, and a dropped private-worker
acknowledgment reconciled to one original effect. Final aggregate commands and
artifacts are still required before completion.

The application fixture requires genuine fresh Basic host authorization. Its
reviewed preparation uses fresh configuration/runtime/archive namespaces and
explicit indexed test entry/unit deltas for external Hub/storage injection only;
installed package bytes and real helper/peer/guard checks remain unchanged.
The owned guest may select a fresh.32 fixture only after preserving the quiescent
original.30 selector/unit identities and all WEB015 pending evidence. This is
an isolated application fixture, not a production selector or guard change.

Pre-smoke source freeze `2b6e329d2ccd3c716cb416c956379895cbb66a7e50067b1e0ebc668955302d97`
contains1473 regular inputs, with five explicit task/plan/evidence bookkeeping
exclusions. All1473 inputs matched the build at that freeze. Owned native
fixture0.2.32 builds the matching UI/wheel/shared image; canonical version remains
0.2.2. Actual pinned UBI10micro ancestry and a read-only, no-network UID981
container verify no Node/package managers. Image
`47ea06111626a86869ccd69800061ae095ea212f5db24b2d7cc7b362b69471fb`, UI manifest
`163e731d15c622c9e2e5a9f8f6d58f870e20dc103c5d9c564fd7340c9982401f`.

Actual native staging passed6.332s with114 installed Python modules byte-exact.
Fresh local storage simulation setup passed2.095s; new archive
`f7b7fbbf-8826-46d6-97d7-4c0b384a56b2`. Original WEB015 configuration, pending
application, key, history and API store metadata remain unchanged. The first
proposal-only fixture draft refused an incorrect `main` entry-point assertion;
the actual generated entry is `hfcache.cli:app`. Its script/log/three proposed
fragments remain retained. Versioned proposed-v2 passed0.902s, owned installation
2.043s and fresh profile preparation2.068s. No API/helper/worker/Caddy role had
started at this checkpoint; actual supported Basic permission proof and browser
effects are still required. Evidence: `/var/tmp/web-016-validation-2_9zjimp/`;
build artifacts: `/var/tmp/web-016-artifacts-2_9zjimp/`.

The original browser plan covered36 normal cases (12 per engine), followed by nine
separate busy/partial/integrity cases using the real archive lock, an external Hub
repository refusal, and last-only owned publication damage. Actual final results
are recorded below; syntax checks and peer review alone established no acceptance.

Installed normal4 now actually passes432.496s: all36 one-attempt cases across
Chromium156.0.8078.4, Firefox157.0 and WebKit27.2. Thirty original keyed operations
finish exit0 (nine sizing, three selected sync, nine real Unix verification,
six diagnostics, three offline refresh); two exact publications and12 reports
are checked. Three real pre-header connection aborts recover the original key
with zero replay. WebKit genuinely pages25/5/25 rows, retaining known loaded
extent30. All72 CSP checkpoints are empty; no browser dialogs/popups/page errors.
All13 original process pairs are gone, four cgroups empty and five endpoints
refuse after normal stop; original WEB015/baseline/fixed inputs remain exact.
Cohort `c5206a2897514cbdac62b7c62377e2b8`; collected root RESULT SHA
`ee6fe410eb50bff3cafec4cc12ede6084cdc6c1e86ad8b761445805492882612`,
browser REPORT SHA
`9ce7cbf1e80e953a7a8a8278920830ea1b30392d7fa31e63e586a2b7b3b0a965`.
Safe locators are `functional-normal4-{result,browser-report,summary}-observed.json` in
the evidence directory above. Normal success alone does not complete this package.

The three supplemental cohorts also actually pass, one case per engine per mode:

| Actual cohort | Elapsed / outcome | Root RESULT SHA256 |
| --- | --- | --- |
| busy1 `a16b9d13ddfc472dbb366a20933c3741` | 174.941s; three failed20/HFMNT010 originals, benign busy/no invented report; real holder released/reaped after roles stop | `e537305a06c7bcfc74a6bb385cd319accde43252698796dbe1804bdca99f9a09` |
| partial1 `465e44ee969049f5868a731886c7b818` | 106.298s; three failed30 originals preserve dataset HFHUB001 and model skipped/HFWRN011/original publication; exact reports | `8284b3a3ad5a46a909a6c0fc6ecd97b35278a0054ac877da0e853da9d8912c22` |
| integrity1 `7bccd27c72c740e3a16efc52c445916b` | 100.423s; three failed40/HFVER001 originals and exact real Unix worker/result/report joins; no healing | `993f82429023302a7e428522a764d0bc1e8599685f720bd470f344f491a35b65` |

Each original has exactly one POST, authenticated failed-result presentation and
zero replay. All roles normally drain with known cleanup, four empty cgroups,
five refused endpoints and unchanged WEB015/baseline/fixed inputs. Final damaged
model publication `c76106ccf7894c488c92a6b23f27a83b` remains damaged at
`config.json` SHA256
`7c064c316c677e2d1330869e1639194066cf8ca00f8bd3631fd3891213152481`;
no later sync/repair is run. All45 cases are one-attempt, with39 original jobs,
509 trusted passive requests and90 zero-CSP checkpoints. Final durable report
count18 includes three partial and three integrity reports, no busy report.
Evidence is `functional-{busy1,partial1,integrity1}-{result,browser-report}-observed.json`
and `functional-all-summary.json` under the evidence directory. Five actual
synthetic screenshot copies have verified bytes/mode0600 under
`private-screenshots/`, manifest SHA256
`e177f72eb574f5e4856ae7adf681cfdb3e1767715fe7cd433667a7e3e9b8eb28`.
OPS06–09 now reference44 verified executable source nodes and these actual
functional executions; final strict-gate acceptance remains required before
row/task completion.

Strict gate1 actually failed1652.720s with no source drift:8599 backend tests,
3556 web unit tests and historical frontend checks passed, but one existing native-fetch
component assertion expected a globally unique operation ID after the new result
view intentionally repeats the original receipt ID. Its original log/result
remain retained, not promoted. The correction scopes assertions separately to
the original recovery receipt and authenticated result while retaining the exact
two-GET/no-POST and native fetch receiver assertions. Focused2/2 and full
frontend3798/3798 pass; no skipped tests,95.55% line/90.36% branch coverage.
Actual precheck artifact: `web/.artifacts/component-NwDHJa/report.json` and its
coverage directory. This is a test correction, not a runtime or response change.

The full gate2 ran against source
`8428ed589227ac3057840aeaa7d44597234cc934f42a9998b015851a100448b6`,1473 inputs.
`source-transition-test-assertion-only.json` proves that only
`web/test/native-fetch.component.test.tsx` differs from the installed functional
source; all other1472 inputs, runtime/API/UI/packaging/human documentation and
functional fixture bytes are unchanged. The existing wheel/UI/image and45 actual
functional results remain correctly attributed to source2b6e329d…; no destructive
operation is replayed to retest an assertion-only change. Five bookkeeping
exclusions remain unchanged.

Gate2 actually failed1233.876s, with no source drift:8598 backend tests passed;
the unchanged real scheduled-observer SIGINT case timed out waiting10s for its
child after original-handle observation. Its original child was killed/reaped by
the existing test's failure cleanup; this failed gate is retained, not accepted.
The exact two-signal focused test then passed2.80s. A separate local diagnostic
adds only a child faulthandler dump before the unchanged timeout and runs the
exact existing SIGINT test20 times:20/20 passed12.397s, no stack dump. Evidence:
`signal-diagnostic1.{py,log,result.json}` in the evidence directory, result SHA256
`9fb4b35e56519cfb98c5c62efe0f75637b7149dbe77683308640c954728dbd97`.
Those diagnostic passes neither explain the timeout nor replace a strict gate;
bounded phase sampling is in progress before deciding whether a source/test fix
is justified. No timeout is raised and no required test is skipped. A complete
strict gate remains required before commit.

Phase diagnostic2 sampled64 real SIGINT deliveries at eight bounded offsets:
64/64 passed40.261s, still no explanation of the original timeout. Diagnostic3
then injected one real signal immediately after the actual HTTP pool lock was
acquired. It reproduced a10s timeout; its7s stack shows close blocked re-acquiring
that lock. This proves the asynchronous-interruption failure class, while the
original gate's exact cause remains unproven without its own stack. Preserve
`signal-diagnostic{2,3}.*` and `signal-diagnostic3-child.stderr.txt`, SHA256
`1b6f3478bf144120cd50cde2eb7fa9ce04c9f061ba28510e528a7b6b17f35282`.

The scoped observer correction now latches signals and raises at owned safe
checkpoints, including before fresh POST, terminal completion and actual pending
unlink; stop-aware sleeps use at most0.1s slices. Existing client.py, HTTP budgets,
wire formats, locks and default imported-library behavior are unchanged. Real
SIGINT/SIGTERM lock-entry regressions, ordinary signals, terminal success/failure
and pre-unlink preservation, fresh-submission refusal and long-wait checks pass
within258 focused scheduled/client/adversarial/socket/config/redaction tests9.09s.
Ruff, formatting, Pyrefly and independent source review pass. Human client guidance
and ADR121 state the cooperative interruption contract; documentation alignment
passes215 human documents/27 helpers. The first ADR prose check refused execution
IDs/agent links; those audit details are retained here and the technical amendment
now states only the standing decision and source/test evidence.

Fresh current source freeze
`d5b17c5b32a8665bb2e61114e79e260023be821babd4b83bf0d75d74bcdf5b0e`
contains1473 regular inputs. Relative to gate2, only the scheduled-client module,
its tests, human client guidance and ADR121 differ. Strict gate3 and new native
fixture0.2.34 build actually started; build artifacts target
`/var/tmp/web-016-current-xiasl8_m/artifacts/`. Original.32 artifacts, damage and
45 passing cases remain predecessor evidence, not substituted for current-runtime
acceptance. Fresh WEB016b runtime/archive/stores will reuse the same guest,
Caddy/browser engine and proven fixtures, preserve all WEB015/.32 originals, run
the45 UI cases plus installed CLI stop observations, and leave integrity last.
These new build/functional/gate results remain pending until actually observed.

Source3 gate3 actually passes1494.761s with1473 inputs/drift[]:8608 backend tests,
52 unrelated opt-in deselections,3556 web unit/3798 combined React tests,95.55%
line/90.36% branch coverage,581 historical frontend unit/110 mounted checks, strict
format/lint/types/contracts/docs/build/browser/read-fixture and all locked wheel
profiles; no required skips. Result SHA256
`7aeea2cf1ba2b3a9101d651d84c40f92850a49cd2c259f406d6788fed5ae51bc`.
The.34 build and pinned UBI10micro/no-Node checks pass. Stage7.710s matches all114
module bytes; all six fresh setup/provisioning phases pass with477 original
objects unchanged. Native.34 archive UUID
`deae8dab-aa8b-4a3d-ab0b-fd39699b60fb` remains retained.

Current.34 normal1 actually fails186.715s after Chromium12/Firefox10 cases pass,
with19 original operations and known normal cleanup. Firefox's history assertion
reads its label, list and row count across separate awaits; operand values were
not captured, so that failure alone cannot identify a rendered invariant breach.
A synchronous store-subscriber regression then independently reproduces ready
rows3/loaded extent0: query-ready publication precedes its awaiting caller's
count bookkeeping. The minimal source fix derives the active count from the same
ready query snapshot while preserving prior cursor counts, budgets and
generation. The new regression covers every published ready Ops/Runs state over
first/next/previous/refresh. The versioned browser test samples one atomic DOM
tuple, records its operands and immediately refuses any bad ready invariant;
it never polls past a violation or relaxes25-row/32-position/800-extent bounds.

Retain failed.34 cohort `a8e392988956410185d75d2a63114264`, root RESULT SHA256
`43901f7e0f74295b0b117f10a6fdedd2c969cf465ffc683d4f3ca4c6c257fa71`
and REPORT SHA256
`d21c2e5ee3b072ee7ffdb7719fbee500eb4bee5a360ad2929692f9a919311017`.
Its19 original keys/receipts and completed Chromium transport ARM/abort evidence
remain unchanged; the prepared normal2 descriptor was never uploaded/launched.
The separately recorded positive new-verification case hashes two repositories,
two revisions/four objects/86 bytes, but the overall failed cohort is not accepted.

History/state236 focused tests and independent review pass. The first full
frontend precheck retains3798 passes/one existing detail URL-effect assertion
failure; its store-ready wait preceded React's URL effect. Waiting for the exact
expected pinned URL preserves that assertion. Full frontend precheck2 now
passes3799/3799 in62.008s,95.55% line/90.37% branch, no skips; types/lint/format and
docs215/27 pass. Current source4
`7fa3bb9fc999132736df13f7faac9e73033efcb80a4214e40bf2b6d5e4a51f8b`
has1473 inputs and only five source/doc/test changes since source3. Gate4 and
fresh.36 artifacts started; target
`/var/tmp/web-016-source4-nnvkh05d/artifacts/`. Fresh16c reuses the same guest,
Caddy and engine while preserving old15/.32/.34 state; mask72 adds only its fresh
physical runtime to existing masks70/71. All current47 installed UI/CLI cases and
gate4 remain pending. No old passing cohort is promoted to current source4.

Earlier attempts remain false and retained. Normal1 failed2.693s before browser
or POST because the fresh native units had incorrect existing-policy file labels;
exact owned files were provisioned with the required systemd_unit_file_t, without
a permission grant. Normal2 failed63.604s before browser/POST: importing the
external storage fixture opened a character descriptor before the stock worker's
FD3 audit. A versioned fixture entry defers only that external adapter import
until after the unchanged stock bootstrap audit; worker/package predicates stay
unchanged. Normal3 failed31.722s on its sole original sizing operation
`8e82a8291a7ceffe0ce70b0fab9318a5`: actual HFAPI015/exit20 waiting-budget expiry,
not a command effect. Fixture-only sync wait2s was shorter than actual host
authorization2.817s; versioned v3 changes only that budget to30s. Its original
failed receipt/result and every predecessor script/config/index/policy/receipt
remain preserved, with no resubmission of the original key. Actual guarded
revisions and diagnostic logs are retained under the evidence directory; these
fixture failures do not establish product acceptance or new platform proof.

Human documentation is implemented with the feature: `docs/web-ui/operations.md`
explains every job's prerequisites, scope, archive/Hub effects, actual permission,
admission/result/report distinctions, loaded-history limits and original-handle
recovery. Entry navigation, troubleshooting, API-backed client and discovery
references match the implemented labels and offline refresh semantics. The real
normal browser workflow follows these labels from Jobs through result, report,
repository Activity and original-key recovery; existing captures remain private
synthetic evidence. No future screenshot or documentation-only task substitutes
for this workflow. The full gate runs documentation alignment and link/examples
regressions; its final result remains pending here.

Reviewed INV006/007/013/014/018/020/021 and relevant
ADR109/115/116/118/120/135/136/137/145/148. Existing authority, classification,
private-worker, bounded-read and original-handle rules remain applicable without
a new endpoint, durable format, runtime dependency or privilege. Dated composition
amendments in ADR136/137/145 document the browser's job, history and report owners.
The current response wrapper remains bound to current policy; only the nested
durable report may carry its historical fingerprint, covered by five strict
client regressions. There is no client authority exception for old reports.

## Completion evidence

Completed 2026-10-26, WEB-016, this commit. Earlier execution notes above are
chronological predecessor evidence; the following is the final current-source
acceptance. The executable test nodes and executions for OPS06–09 are recorded in the
[acceptance ledger](../support/web-ui/acceptance-evidence.json).

**Current source and strict gate.** Source
`7fa3bb9fc999132736df13f7faac9e73033efcb80a4214e40bf2b6d5e4a51f8b` (1473 regular
inputs) passes `historical gate invocation (original command SHA-256 `dfe15d4ee16e8207e5ddfe1138f7416950f8e6013a5d77e8aa230bfd51dccdc4`; Git `c692d7ae4b866fefd8a743a21afdb729da0f39c4`)` with exit 0 in 1781.806 seconds.
There is no source drift and no required skips. Results include 8608 backend tests
with 52 unrelated opt-in deselections, 3557 web unit tests, 3799 combined frontend
tests, 95.55% line and 90.37% branch coverage, 581 historical frontend unit tests and 110 mounted
checks. Formatting, lint, types, contracts, locked wheel profiles, builds, browser
and read-API checks pass, as do documentation checks for 215 documents and 27 helpers. Evidence
root `E=/var/tmp/web-016-validation-2_9zjimp`; `E/gate4/strict-gate-result.json`
SHA256 `b1ba833b1f0bc3c215c4bb86a3704eb72ff41ab6ee52eee79021fbdda5407df3`.
Only the five declared bookkeeping exclusions may change after this gate.

Post-gate metadata validation passes with 78 tests in 10.11 seconds across
`test_web_plan.py`, `test_docs_alignment.py`, `test_docs_config_contract.py` and
`test_docs_migration.py`; `scripts/check-docs.py` confirms 215 human documents and
27 helpers, and the frozen 1473-input comparison reports no changed, new or
removed source.

**Matching installed artifacts.** Native fixture 0.2.36 uses
`/var/tmp/web-016-source4-nnvkh05d/artifacts/`; canonical project version stays 0.2.2.
The source/wheel/UI checks match the 114 installed modules. Shared image
`3da0c7945c63b0ae0c1e357c70481201d384a8f02350b27b5813c985ed733c57`
and UI manifest
`b0fb06f819ea87b89ed0fd96472b66a93c724dcc2e4120b0e56de03264188c46`
have actual pinned UBI 10 micro ancestry. The image probe runs as UID 981 with a read-only root and no network.
It finds no Node or package managers; `E/source4-image-no-node-proof.json`
SHA256 `7c89cd959e34fb681a19a2f1a5b639688061b33f0a958c28dccb3193fcf4f9e8`.

**Current installed acceptance: 47 one-attempt cases pass.** Tests run in the same
owned guest through real Caddy TLS, Basic authentication, API, helper and FD3
worker. The installed application service code uses a fresh
`LOCAL_STORAGE_SIMULATION` archive, with only declared external Hub/storage and
transport-loss fixture seams. No production services are touched; this is not NAS
or new rootless/platform acceptance.

| Actual current cohort | Cases / elapsed | Result SHA256 |
| --- | --- | --- |
| normal1 | 36 across Chromium 156.0.8078.4, Firefox 157 and WebKit 27.2; 481.193 seconds | `4ef61065b5527bd2cd1222c17fd16696ad243d42d73a11f80c780b8a555cd03a` |
| busy1 | 3; 173.482 seconds; exit 20 / HFMNT010 | `1a2a9e3181d3d118313ea12a064bc71ea526ce4388b2acb1cb81eabd9c0a0563` |
| partial1 | 3; 109.008 seconds; exit 30, with failed dataset and retained model results | `4dff655c8c0decf93bff7823f34d513df3e10d4e5101b75553a3c47e78f5e532` |
| observer2 | 2; 73.710 seconds; actual SIGINT/SIGTERM stops, coordinator exit 0 | `e5ed892a7a76caa68014fadbd410797dfd200804d35d272752da20c8dfaaef8c` |
| integrity1, last | 3; 89.241 seconds; exit 40 / HFVER001, with no healing | `0d4aaa0890b41ba6d605f78516a92e8ce6d6954e3cf8725bd965c71371107433` |

These are `E/functional-source4-MODE-result-observed.json`; combined evidence
`E/source4-functional-all-summary.json` SHA256
`45445e561e091d74b81af965344532f00c9ac51aeeb59946510e8b928be85da5`.
Pinned owned-SSH execution uses `/usr/bin/python3 -I -B
/home/webfixture/web016c-inputs/web-016c-run-native.py --descriptor
/home/webfixture/web016c-inputs/source4-functional-descriptor-MODE.json` for
normal1/busy1/partial1/integrity1 and `web-016c-run-observer-v2.py` with
`source4-functional-descriptor-observer2.json` for SDK2, via noninteractive root
and bounded secret stdin; no credential appears in arguments/evidence.

The 45 browser cases have 39 original POSTs, 516 trusted requests and 90 empty CSP
checkpoints. There is no interception, retry, overflow, dialog, popup or page error. They exercise
all job DTOs, authenticated exact results, real worker verification, genuine
pre-header response loss and GET-only recovery, reports reached from Repository Activity through Operations, and actual WebKit
paging with 25, 4 and 25 rows and a loaded extent of 29. SDK2 separately
submits one original verification, then both installed observers issue only GETs,
restore prior signal handlers and preserve exact pending/lock evidence while the
actual backend continues and returns exit 20 / HFMNT010. The final 18 durable
reports remain exact.
The last damaged model publication `305babbfa6b348c1b38bcd136df7e5ae` retains
`config.json` SHA256
`7c064c316c677e2d1330869e1639194066cf8ca00f8bd3631fd3891213152481`.
No sync or repair follows. All original roles stop normally, cgroups are empty
and endpoints refuse connections. The 667 old WEB015/.32/.34 objects and five
infrastructure pairs remain exact. The owned selector is .36; old selector, unit
and runtime inodes remain retained.

**Retained failures and safe closure.** Earlier failed gates 1 and 2, passing predecessor
gate 3, .32 acceptance/damage, .34 failed cohort/19 originals and all fixture,
precheck and causal diagnostics remain separately attributed. SDK1's original
collector result retains passed=false and cleanup_unknown=true; no acceptance flag is rewritten.
A no-effect retrospective closure verifies its 16 original process pairs, empty
cgroups/endpoints, inputs and pending state without replay:
`E/source4-observer1-retrospective-closure.json` SHA256
`0d16faf2b6333ddffb68b23f91cca71e58a9f700589d3faca8cd481c3c33a095`.
The private v2 collector corrects only protected-controller versus public-input
ownership and a fresh SDK2 proves the required workflow. The old WEB015 pending
application, old .32 damage and both SDK pending handles are not replayed or cleared.

Human Operations, troubleshooting, entry, API-client and discovery guidance is implemented
with the feature. Five actual current private PNGs remain unpublished;
`E/private-screenshots-source4/manifest.json` SHA256
`0cc22966775af98d50f3a123a212fbb26aa041e1ae7689c817a73e9ed88b06cf`.
Representative exact source nodes include the new subscriber-time history test,
`test_web_operations_worker.py`'s real API/Unix all-mode and lost-ACK tests,
`test_scheduled_client.py`'s real signal/lock-entry tests, plus typed job/result,
queue/conflict/large/event/expiry tests mapped in OPS06–09. Review covers
INV006/007/013/014/018/020/021 and ADR109/115/116/118/120/121/135/136/137/145/148;
Amendments to ADR121/136/137/145 record cooperative stop and bounded composition.
No endpoint, dependency, durable format, privilege or architecture decision is added.
