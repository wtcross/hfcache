# WEB-020: Harden end-user workflows, accessibility and bounded performance

| Field | Value |
| --- | --- |
| Status | completed |
| Plan | [Web UI replacement](../2026-10-20-plan-web-ui.md) |
| Phase | P5 |
| Depends on | [WEB-019](web-019-administration-and-diagnostics-ui.md) |
| Branch | `feat/web-ui` |
| Work-package commit | WEB-020, this commit — `WEB-020: harden browser recovery, accessibility and bounded reads` |

## Read before implementation

All new screens/controllers; acceptance cases; real functional harness; testing browser/a11y/performance budgets.

Also read the relevant sections of [architecture](../support/web-ui/architecture.md), [API contracts](../support/web-ui/api-contracts.md), [testing strategy](../support/web-ui/testing-strategy.md), [acceptance matrix](../support/web-ui/acceptance-matrix.md), and [human documentation map](../support/web-ui/documentation-map.md). Load only affected living contracts and ADRs through their indexes. Refer to the [source review](../support/web-ui/source-review.md) for pinned baseline evidence; current git wins over it.

## Scope and implementation requirements

Complete the cross-browser matrix of Library/detail/README/tags/config/jobs/maintenance/admin workflows over real Caddy/API. Stress changing current pointers, slow responses, auth/authority changes, large manifests and route churn without mixing data or retrying writes. Test new server/UI contract mismatch with an old open page.

Apply automated accessibility checks and manual keyboard/screen-reader smoke to tables, filters, dialogs, validation, global recovery and content views. Fix focus order/restoration, announcements, semantic names, contrast and responsive/zoom issues. Use reduced motion and no network fonts. Ensure virtualized content remains operable.

Measure bundle size, initial usable Library, long tasks, DOM/memory bounds and polling on a fixed realistic synthetic fixture. Optimize avoidable per-row requests and lazy-load costly renderers without new aggregate endpoints. Enforce declared coverage/bundle/performance targets; record observed hardware/browser/data, not universal performance claims. No unchecked flaky-test retries or silent acceptance target inflation.

## Unit and component validation

Run full new frontend unit/component coverage and critical branch mapping; regress every discovered bug with a focused test. Verify coverage exclusions cannot hide security/controller code.

## Integration validation

Run slow/cancelled/stale/large-response loops against real API pools and assert bounded request concurrency, response work and retained memory. Decode large integer and limit failures safely.

## Functional validation

Run Chromium/Firefox/WebKit, 1440px/390px and 200% zoom, keyboard dialogs, screen-reader smoke, hostile README network inspection and 100 route/refresh cycles. Record target budgets and resolve serious/critical accessibility failures.

## Human documentation deliverables

Document browser support, keyboard/use patterns and practical large-library limitations. Correct any guide label/screenshots discovered inconsistent during real workflows.

## Acceptance

Cross-browser functional, accessibility and bounded-performance acceptance has actual evidence; the UI remains safe/usable under races, large data and interruption rather than only happy-path screenshots.

The task also requires the existing `scripts/check.sh` gate plus strict applicable web/Cockpit and functional checks described above. New capabilities are not completed solely by adding test descriptions. Update actual test-to-case mappings and run them. Documentation and relevant contract/invariant/ADR updates land with the behavior, not in a later catch-up task.

## Execution notes and blockers

**Completed 2026-10-29, WEB-020, this commit.** All six owned rows and the final
required gate pass. The detailed execution checkpoints below retain their
original statuses; [completion evidence](#completion-evidence) is authoritative.

### 2026-10-29 rejected-handle reader announcement fix

The real Firefox157/Orca status-only run in
`/var/tmp/web-020-actual-reader-s248grsi` keeps native focus on **Save original
handle** after submitting an invalid handle. The correct local failure is visible,
no operation is submitted, but the full Orca log never announces that failure;
only the entry-valid feedback is spoken. All original desktop processes close
normally (35.544s, no timeout). The earlier seven-surface reader run remains
scoped evidence for its actual named controls, table, README, validation and dialog;
it is not a requirement to read every expanded warning paragraph automatically.

Actual seven-surface report `f03688a1…`/28544B and natural status-only report
`8a55fd66…`/4773B are retained in the UX-02 ledger with original flags and
separate outer closure; no worker wait status is invented.

The importer now retains a typed success/error message: rejection is an error
alert, while successful original-handle storage remains a polite status. Focus,
original handles, authority and HTTP behavior are unchanged; other recovery
messages are outside this correction. Review of INV-021 and decision145 confirms
this is presentation of an existing local failure, with no new invariant,
architectural boundary, payload, grant or runtime dependency.

The existing real-App component regression now checks rejected import alert,
retained Save focus, no request or stored record, then a valid import clearing the
alert and preserving polite success and normal handle/copy recovery. All nine
`OperationRecovery.component.test.tsx` tests pass in7.64s using
`pnpm --dir web exec vitest run --project component test/OperationRecovery.component.test.tsx`.
Both TypeScript configurations and formatting of the two changed source/test
files pass. The matching Native68 installed-reader recheck now passes, as recorded below.
The complete changed-source product gate remains required before task completion.

UX-02 now completes from prior actual seven-surface `meyymo95` plus the
Native68 specific error-announcement pass `dum9rf2m`: the browser verifies68/
manifestac39/wire320c, and genuine Orca speaks the full rejected-handle failure
including **No operation was submitted**, with Save focus retained,0POSTs/page
errors and790854 PCM bytes (284623nonzero samples/peak30308). Original report
is6060B/SHA `adf35cb38477961326af168e0925f1983852d2431dd65de9cf4321ca68a6be68`.
Outer Root93690 closes normally in37.526s (parent0/timeoutfalse/allownedclosed,
SHA `d80b9a8c…`); original worker reviewedfalse/readerreapedfalse stay unchanged.
The ledger maps existing component/API checks and actual reader/keyboard/axe
scopes without claiming human listening or full contrast/conformance.

All six owned rows are complete, but WEB-020 remains in_progress/uncommitted:
required changed-source full gate2 (Root86932) is still running. Prior5d1 green
results are historical. Native68 build/stage/switch/HTTP pass at canonical
`610de3ca…`, UI-build274933cb/manifestac39b9d1/wire320c; the post-build ADR
label/link correction changes no app/runtime bytes. Its complete JS inventory is
253846 gzip bytes (entry204530/lazy49316) below358400, with no new p95 claim.
Review of INV-021/ADR145 finds a local message-severity correction only: focus,
original handles/authority, no-replay HTTP, wire/storage formats and dependencies
are unchanged. No new architecture/invariant is introduced. Human docs stay
frozen. Do not complete the task, commit or select WEB-021 before gate2 passes.

### 2026-10-29 direct application checkpoint

The user explicitly redirected work from repeated test-harness validation to
testing the actual application. Stop new harness models, inverse/default checks,
source packets, binders and review loops. Preserve the existing drafts and failed
records. This changes execution method, not the required functional acceptance;
WEB-020 remains in progress and uncommitted, and WEB-021 has not started.

Direct inspection found Race11's first old51 helper startup failed with
`233/RUNTIME_DIRECTORY`: the documented `/run/hfcache-host-helper` runtime
directories were missing. The owned guest received only the documented
Root:Root 0755 parent, Root:hfcache 0750 (GID 983) API directory and existing
`hfcache_host_helper_runtime_t` labels through `restorecon`. No policy or unit
hardening was weakened. The helper then started successfully. Evidence is retained
under `/var/tmp/web-020-validation-nvj5zeg7/direct-installed-app-start-d594202b887f43bb9acf7d6b3d394401`.
The original Race11 failed/unknown flags remain unchanged.

The direct old51 API returned authenticated health/catalog reads at its actual
`/management` prefix; bearer HostStatus 403 preserved the administrator boundary.
After normal service/socket drain, the original retained helper unit was restored
and the official installer switched to the already prepared 0.2.63 target.
`direct-return-to-prepared63-0230b2bf95914cfbbfe09dbfc46bd3ac` records this return.
It is not upgraded-A/race acceptance or a successful nine-case Restored63 record.
The helper, verifier, API and existing shared Caddy then ran normally; the API had
its canonical Unix socket and 127.0.0.1:8787 listener. Enforcing/noNFS/base5 remain.

Direct Basic-authenticated health, catalog, native HostStatus, UI HTML and
bootstrap all return 200 through the real Caddy endpoint 22443
(`direct-new-app-http-53590f1f23b14bdab50791e7989b422f`). HostStatus reports
supported native authority and all six archive/Hub/control/schedule/configuration/
observer grants. These facts do not substitute for actual guarded effects.

All three stock browser engines pass real trusted-HTTPS Library/Operations/
Administration navigation at 1440px/390px, with no JavaScript errors, server 5xx
or POSTs and normal browser/context closure. The original record is
`direct-browser-application-071ec096519847eb970b5b6c531e3663`. Those initial
screenshots show early loading and do not prove loaded workflows. The later
`direct-browser-application-7217426a97a1403a833a6f73d80bf5ea` report records
all three engines loading 240 Library repositories, searching `owned/model-000`,
and reaching the 3997-file manifest in the same SPA Document. The table exposes
aria-rowcount 3998 with only 10 mounted data rows; keyboard End and file 3997
inspection show `config.json`/3bytes. No JavaScript error or POST occurs in these
completed checks. Its aggregate script remains false because the subsequent
HostStatus assertion misread the response envelope. A separate Administration
continuation likewise retains its original false result after selecting Chrome's
HTTP 401 challenge response rather than the authenticated 200. These are script
issues, not application bugs; passed data checks were not replayed to repair them.
The later configuration and upgrade outcomes are recorded below; neither is accepted.

A genuine product bug was found independently: archive health classified the
documented `published/{repos,manifests}/{models,datasets}` directories as four
unknown entries, despite ready/valid policy. The fix in `src/hfcache/archive.py`
recognizes exactly these optional post-sentinel namespace roots and treats them
as opaque. Required initialization layout, symlink/unknown-sibling refusal,
no-sentinel checks and bounded/no-payload traversal remain. The 153 focused
archive/init/publication regressions pass in 18.13s, with Ruff passing. The
first full gate remains failed because the audited archive module pin was stale;
its required source-pin update and regenerated browser contracts preserve wire
shape. The subsequent complete `scripts/check.sh` gate2 exits0:9039 tests pass,
52 are deselected in 1196.62s; frontend, Cockpit, installation/build and all other
required checks also pass. Original stdout/stderr are
`/var/tmp/web-020-validation-nvj5zeg7/direct-application-fix-gate2.*`.

Native 0.2.65's retained build remains unqualified/inactive. The final native66 source
snapshot is `5d1fbe6e22511f0dec14c31adc87b30d4d1cab02bdedeb08d334e88372289607`;
wire digest is `320c5fb14547082d5e6a1cee8009406deb1dab7af6a155a9df5b1476ab82aec9`.
Native 0.2.66 is actually staged and normally switched/started, with helper 25579,
verifier 25605, API 25613 and shared Caddy 25619. The original switch is
`/var/tmp/web-020-validation-nvj5zeg7/direct-web-020-native66-switch-f74ca0774f69459ab2ef21c09c5a9f7c`.
Actual HTTPS evidence at
`/var/tmp/web-020-validation-nvj5zeg7/direct-web-020-native66-http-d83eb9c0d0774ad6a0eaec1b8b4cd11d`
reports health 200, ready/policy_valid true, archive initialized,
unknown_entries=[]/count 0, supported native HostStatus with all six grants and
matching 0.2.66 UI/bootstrap. This retests the installed classification fix. Rootless 0.2.67
is built only; no guest acceptance is claimed for it.

The original succeeded preview `e4fb1f4f5c88df01dbb7b64a8e5c02b4` and interrupted
Apply `1b808e75638c6894b20eaa4289022971` remain in the operation store. Apply's
transmission event exists and its original application key is lost; no replay or
successful configuration application is inferred from the unchanged current file
or missing physical pending marker. Upgrade attempt `e41f6f0…` also stays false:
Root began the switch before all three old pages were ready, Firefox received
connection refused and WebKit was not reached. This failed original is preserved;
it is not an application regression claim.
The later ready-before-switch upgrade passes separately, as recorded below.

Direct native 0.2.66 original-operation recovery passes all three engines with raw
exit0 in `direct-browser-application-27fad989d8e44dadbc25f55d609d6580`.
`.scratch/web-020-direct-app-recovery.mjs` imports the original interrupted Apply
by ID, observes interrupted, reloads with the same retained ID and confirms both
new diagnostic buttons disabled. Each row records zero POSTs/page errors. This proves
ID-based observation and browser retention, not recovery of the lost key or a
confirmed protected outcome. Original stdout SHA256 is
`e3f4833444edaae5eaf21f654fc83c94232897ce6ddd720e0877b113d69d025d` (8394B).

Native 200% zoom covers seven surfaces: workspaces, Library table/filter, archived
README, status, original recovery, configuration validation and unsaved dialog.
Chromium/WebKit pass in `direct-browser-application-aaf812d054dc48b5a3213c94bea2032b`
(source `.scratch/web-020-direct-app-zoom-current.mjs`); its aggregate exit1 is
preserved because Firefox Playwright pointer activation fails. Original stdout
SHA256 is `837a1ac048f2833d16246a138df857c4bcd8a85ea938df290619e9bf91e3b508` (6511B).
The separate Firefox-only keyboard run
`direct-browser-application-f3c0a3cca3d64c92acb2fd157bdf978e` exits0 with all seven
surfaces passing; source is `.scratch/web-020-direct-app-firefox-zoom-keyboard.mjs`.
Its 1×1440×1000 / 2×720×500 CSS viewports retain the same 1440×1000 native PNG size,
with CSS zoom 1/pinch 1. Six actual DOM CSS-coordinate navigation hits are true;
focus/outlines, reachable controls, document overflow and dialog trap/Escape/focus
restoration pass, with zero POSTs/page errors. No Firefox pointer success is inferred.
Original stdout SHA256 is
`2caf488bddb98daee9f75a9e878e89218c537c045093e856f470655f9b152fb0` (2397B).

All these originals are under `/var/tmp/web-020-validation-nvj5zeg7/`, with evidence
in each `originals/original-002.stdout` and the exact reaped command status in its
completion record. They use canonical native 0.2.66 source `5d1fbe6e…`/wire `320c5fb1…`/UI `1faa4d4e…`.
The earlier `79707d485517428b8e3d3472d0acd940` aggregate stays failed (wrong expected
state for the selected interrupted operation; headful Firefox launch failed).
Ledger functional executions retain all raw exits and scope limits. UX-01–03 now
have partial functional evidence/in_progress; UX-03 now has existing component/API mappings; actual reduced-motion/external-font/390px
coverage remains pending.
No new test node or completed row is invented; reader acceptance remains open.

A subsequent direct old63→66 upgrade passes all three engines with raw exit0:
`direct-browser-application-16210ea871704954a01b481d068c654c`, from
`.scratch/web-020-direct-app-upgrade.mjs`. All three old pages were ready before
the official66 switch. Explicit Reconnect keeps each old Document marker while
showing **Interface update required** and clearing private API/HostStatus
observations to unavailable. Explicit reload then connects to66; every row has
zero POSTs/page errors. Both original operation receipts remain in the backend;
no configuration application is replayed. Original stdout at
`/var/tmp/web-020-validation-nvj5zeg7/direct-browser-application-16210ea871704954a01b481d068c654c/originals/original-002.stdout`
is6710B/SHA256 `464eae7406d7394422fd6e0cad0474b29b367b6aa27de61374845c5a51eeb470`.

The preceding official roundtrip to63 is `32d2cef5…`; the final roundtrip to66 is
`2428a034…`, with helper30749/verifier30767/API30775/Caddy30781. Earlier failed
upgrade originals stay false. This is functional evidence for AUTH-10/UX-01,
which remain in_progress; it does not complete authentication changes, all
prefixes/writes, rootless or the remaining required layers/clauses.

Actual native66 offline catalog writes now exist once per engine: Chromium
`0ffe8fcf0df51146d674f13406706a3f`, Firefox
`34d046383a320b6ec34c9c15777bbdb5` and WebKit
`6a4198c1fb65fb36cc2a3000ed09d86c`. Each original receives202 after one POST and
succeeds with domain exit0/**success_with_warnings**, HFWRN011, one captured tag
snapshot, one written observation and zero failed records. Technical evidence
remains partial/unsupported for this fixture; no integrity claim follows.

Raw mutator scripts remain exit1: Chromium's DevTools body resource is unavailable,
Firefox's separate Node observer lacks CA trust, and WebKit's result-region lookup
is wrong. Their jobs are not replayed. Separate original-key/result GETs confirm
Chrome/Firefox saved keys and exact succeeded operations. The read-only all3 UI
continuation `d093bb9f…` exits0, opens **Validated original result**, renders the
actual warning/counts, reloads and explicitly observes the same IDs, with zero
POSTs/page errors. All three mutators are known terminal/closed. Exact originals
and raw hashes are in task020 and the evidence ledger.

CATALOG-09 completes its own matrix/layer requirements using mapped unit/integration,
original Source9 real functional read scopes and current native66 update-clearing,
error/result and recovery observations. Historical Source9 hashes remain unchanged;
no current-source/performance or rootless result is donated. At that checkpoint AUTH-10 stayed
in_progress for one specific installed predicate: the upgrade's old contexts held
no unresolved browser records, so separate recovery/reload and authority-transition
checks do not directly observe a retained unresolved handle across that transition.
Its unit coverage remains valid; this gap is not an Orca/rootless requirement.
The subsequent AUTH-10/UX-01 completions and retained UX-04 scope are recorded below. WEB-020 stays in_progress/uncommitted.

Catalog raw mutators under `/var/tmp/web-020-validation-nvj5zeg7/`:

| Browser | Original directory | stdout SHA256 / bytes | Raw exit |
| --- | --- | --- | --- |
| Chromium | `direct-browser-application-e0721b738d0b45a9844bd4ec95de07f1` | `67b339d4c61db77125c2c9aa693b5402741a8f06926cbf6a985b2b0db2fa6430` /955 | 1 |
| Firefox | `direct-browser-application-256b5f6b9bdb463bad1c181a06ff3cc8` | `00bef5f1a42a27f7d8bfb9d288ed5ac71b878ecfd8d4ba950bcdb71421df04fa` /1114 | 1 |
| WebKit | `direct-browser-application-db96cc7cfa9c49abb803dcf9f3444018` | `db351a1639d5dbf28f139eefa5fe6ab26f510e8f11ac8ff8df005ba839592b46` /1952 | 1 |

Each raw artifact is `originals/original-002.stdout`. Separate Chrome original-key
read `direct-web-020-catalog-original-read-36962527a0e44c7588bf009087330e6c`
retains stdout29835a2c…/3057B/exit0; Firefox original-key read
`direct-web-020-catalog-firefox-original-read-77d5ca8fe97e443db41d413416856bc4`
retains stdout42cb32d6…/3057B/exit0. The all3 read-only continuation is
`direct-browser-application-d093bb9fb9a940fe93689827cb2bdb1c`, stdout
`da8c28929002029df51690aff31622c714fea2e4940d175fce87ffec6cdbc5b9` /5217B/exit0,
from `.scratch/web-020-direct-app-catalog-observe.mjs`. No delivered script is
modified after handoff. Original effect/observer statuses stay separate.

AUTH-10 evidence scope uses mapped unit privacy/reauthorization and real HTTP
integration plus all3 actual native update-clearing, same-original recovery and
key retention; the joined unresolved-handle transition gap above remains.
CATALOG-09 completion uses mapped integer/late-handle unit/integration plus original Source9 core large-table,
real slow/cancelled/timeout/large-byte transport and budget negatives, with current
native update-clearing/result/error presentation. Historical functional records
keep their776470cc source; native66 observations keep5d1fbe6e. Complete rows do not
imply all WEB-020 performance/accessibility/profile acceptance.

Current rootless67 Gen2 negative UI case `56ca7d31…` passes all three browsers,
raw exit0 with normal closure and zero POSTs/page errors. The real Library reports
HFVER007 without an invented table; Administration is unavailable and configuration
GET503/HFAPI022 supplies no private edit controls. Six axe4.14.0 whole-document
scans have zero serious/critical **violations**, while moderate region violations
and serious color-contrast **incompletes** remain. This is not full accessibility,
contrast or positive rootless acceptance: Gen2's global archive is invalid/empty.
Gen3 preparation is separate and has no result inferred here.

Evidence is
`/var/tmp/web-020-validation-nvj5zeg7/direct-browser-application-56ca7d3166fb4516b670cdc67c272762/originals/original-002.stdout`,
7932B/SHA256 `41f35f8c73b2f358a0326ec7c1462c6805e31b47149d79d1de67a4305d5a9d66`.
Ledger executions add only these error-state/scan predicates to CATALOG-09,
UX-01 and UX-02; no status is promoted from this negative run and earlier failed
rootless attempts remain unchanged.

### 2026-10-29 rootless67 populated readonly fixture and normal return

The separate generation3 application check `484da9b4…` passes Chromium,
Firefox and WebKit, raw exit0/normal browser closure. Real catalog reads report
220 matches; Library and model-001's archived README Sanitized source render.
Rootless HostStatus is supported with configuration granted and the other five
permissions false. Each browser sees25 private edit controls, edits a tags-only
local draft, validates its exact base with exactly one POST to
`/api/v1/config/validate`, discards it and observes disabled Maintenance controls.
All three have zero page errors. No Apply, job or write to the readonly archive
occurs. Health returns200/ready/policy_valid, while its writer-health archive
state remains `unusable` under the readonly boundary; this is not an initialized
writer-health or archive-integrity claim.

The complete raw is
`/var/tmp/web-020-validation-nvj5zeg7/direct-browser-application-484da9b44dce4f9badbbdd03ee5b8576/originals/original-002.stdout`,
65904B/SHA256 `b3c17bf76db44892b31b7e387f3ebd6f666299af332b79ddeb39fdb47d4a03d1`.
The companion actual HTTP read is
`direct-web-020-rootless67-http-b42a421decf34c70a73904fb7b66bfe8`,
stdout6931B/SHA256 `6fd1cf4670516668d713ab2aa331a65fef2464024dc0896d3d39134294aca1af`.
Original collector `24ed55fb…` stays false in all three browsers/0POSTs: it asked
for a table named Repository library rather than the actual named region.
Its846B raw SHA is `d0882177ff4c413c1ebba3ff299fd3c554a99737ad73cfdec32a976efd6741f9`;
it is a collector-label failure, not an application failure.

Twelve axe4.14.0 whole-document scans cover Library, archived README source,
validated configuration draft and guarded Maintenance. Serious/critical
**violations** are zero. Each scan retains the moderate `.preview-banner` region
violation; color-contrast is **incomplete**, with55 nodes per engine across the
four surfaces. Every retained check says `nonBmp` / only non-text characters
for decorative glyphs. No full contrast, manual reader or complete accessibility
acceptance follows.

This is explicitly a new independent local fixture for archive
`de787517-cada-4590-aec9-b568d2b20911`, not reconciliation of the old global or
other native configuration uncertainty. Image
`dc8800d7a487174295d5c9c44ef720d2e71a1e8c0eca38c695e4921bbd0e35a2`
derives from stock67 image4198b6, changing only the console's local mount-metadata
hook; canonical67 modules/UI and stock API/worker argv remain. The known native
archive is bound readonly without chown/relabel; this is
`LOCAL_NFS_METADATA_SIMULATION`, not NAS proof or weakened policy.
The original global configuration/pending records and stores remain underneath
private fixture binds. Earlier startup failures stay retained: the fixture worker
initially exits20, and only new instance-lock modes0644→0600 on the same inodes
(`e77e25dd…`, stdout84119694…/324B) and the existing engine-SHM type provisioning
(`cfd0d38e…`, stdout180e3542…/332B) correct documented setup requirements;
no module/permission bypass or lock-body modification is claimed.

Normal precleanup `7bc8046a…` captures original role identities before stock stop
removes the healthy containers, proves role/cgroup closure, removes aliases and
restores the native physical domain-lock label with an honest ctime transition.
Its stdout is0509f678…/229B. Existing normal return `e1e353d7…` selects66 and
restores the original configuration guards (stdout223fe652…/198B). Root retains
all failed generations and original results. The ledger adds only this scoped
functional/a11y evidence to CATALOG-09/UX-01/UX-02; no row status changes here.

UX-04 is now completed from its original Source9 measurements and existing
unit/integration mappings: all three p95 values are 1.877/1.952/1.863s against 2s,
initial requested JS is 205,036 gzip9 bytes against 358,400, and 100 same-Document
SPA cycles plus bounded DOM/query/encoded retention pass without mutation retries.
Matching gate7 records 95% line/90.01% branch coverage. RSS observations and
unsupported Firefox/WebKit heap protocols remain explicit; no heap/RSS ceiling,
universal performance or fresh 5d1 measurement is claimed. Of 189 runtime paths,
final 5d1 differs from Source9 only in `src/hfcache/archive.py`,
`src/hfcache/wire_audit.py`, `web/src/wire/contracts.json` and
`web/src/wire/generated.ts`; read/cache/query/SPA/virtualization/CSS code is unchanged.
The ledger keeps original Source9 hashes/scopes `7e314f6b…`, `bcb52779…`,
`aaf8b4de…` and gate7 `4d74ab04…`. UX-03 gains existing component/API mappings
but stays in_progress for the actual 1440/390/reduced-motion/font observation.
No new test was added or run for this mapping.

AUTH-10 now completes on actual case `94221fa0d73d4adfb5f5ed61bebda6cf`,
raw exit0/normal closure in all three browsers. Each genuine original Basic key
starts unobserved with IDnull and25 private configuration controls. The actual
same66 API/Caddy restart changes instance/authority epoch; explicit Reconnect
clears private controls, preserves the exact original authority/key/IDnull and
makes no automatic lookup or POST. Explicit Observe makes one original lookup
and recovers its correct verified terminal catalog warning result. Zero POSTs/page
errors occur and no key is printed or replayed. Source is
`.scratch/web-020-direct-app-unresolved-reconnect-v2.mjs`; original stdout is
1884B/SHA256 `74be2ec9ea814607b78e6dc12b0dae473c4ad09b512458dfbc4c1bf1311efc72`.
The separate restart43df0/socket MainPID error and f518/immediate readiness
refusal remain failed; readiness/marker080a5ccd succeeds without another restart.
Original configuration Apply uncertainty is unchanged.

UX-01 also completes from the mapped real native66 Basic/read/catalog-write/
upgrade/recovery cases and rootless67 generation3 reads/validation/denials,
plus historical all3 native `/management` bootstrap/deep-refresh/history/prefix
checks. Original prefix generation412ce26a has RESULT SHA `f3b97ea9…`/244192B,
browser report `1d46fd17…`/224940B and local common21 metrics/postverify
`73321b0c…`/`283e5818…`; Source13 identities are retained, not called5d1.
Existing Basic unit/socket integration nodes are mapped, not invented. The
rootless local-mount simulation and readonly health limitations remain explicit.
At that checkpoint AUTH-10, CATALOG-09, UX-01 and UX-04 were complete; subsequent UX-03 completion is recorded below.
No reader/responsive outcome, configuration Apply success or old failed race is
inferred. WEB-020 remains in_progress/uncommitted.

UX-03 now completes with actual responsive case `df3610c0f3de4552874fd422f7da2791`,
raw exit0/normal closure in all three browsers, source
`.scratch/web-020-direct-app-responsive-motion-fonts-v2.mjs`. At both1440 and390,
loaded Library/model001, README source, four workspaces/mobile menu and25 private
Administration controls remain reachable. Real Tab/ShiftTab focus is visible
(3px outline), in bounds, without document overflow. Reduced-motion matches true,
measured transitions/animations are0 and actual font resources/requests/document
font faces/external fonts are0; every row records0POSTs/page errors. Stdout is
20118B/SHA256 `438d830aa1c41cb307322572b2ef379aa3bb490977f56868c4cd7e9d51432701`.
Existing seven-surface native200% Chromium/WebKit and separate Firefox keyboard
observations plus mapped component/API evidence complete the row. No Firefox
pointer or universal accessibility conformance is inferred.

Original responsive `4f9973af…` remains collector-false: Chromium1440 passes, then
390 calls isVisible before asynchronous mounting; v2 awaits the same control within
the unchanged30s action limit. Its2887B/SHA `5320817031b897ea383e9f884cc421a733cd43c505b630ad9220a6fb87499de5`
is preserved; no application defect or erased failure is claimed. AUTH-10,
CATALOG-09 and UX-01/03/04 are complete; UX-02 genuine reader smoke is the only
remaining owned acceptance row. WEB-020 remains in_progress/uncommitted.

Remaining work is reader smoke, final95-case mappings/docs and one WEB-020 commit.
The full product gate2 is already passed; documentation check passes219documents/
27helpers after ADR alignment.
The following earlier checkpoints retain their original evidence and failed flags.

### Retained unqualified reader observations

The following original observations have unknown worker exit status. Their full
records remain historical evidence; they are not known-exit executions in the
strict acceptance ledger. Original worker wait flags and separate outer closure
remain as recorded. No exit0/exit1 is inferred or borrowed from an outer process.

```json
[
  {
    "artifact_sha256": "e2313a77ba39856f141c1572094b8e3b87c9714eda3862cb32700dcdb3a8177e",
    "command": "Root-owned direct genuine Orca/application navigation attempt in /var/tmp/web-020-actual-reader-dc0kti3w; separate outer Root original89255",
    "evidence_locator": ".scratch/web-020-reader-surfaces-dc0kti3w-partial.json",
    "exit_status": null,
    "layer": "functional",
    "node_ids": [
      "/var/tmp/web-020-actual-reader-dc0kti3w/worker-result.json"
    ],
    "observed_assertion": "Original worker remains passedfalse/seven_surfaces_completefalse after480s manual-command deadline (AssertionError). Actual speech proves only Library navigation link, main content and Apply filters button; the other6 required surfaces remain unproved. No test or application failure is inferred. Original reader PID627940 retains reapedFalse/direct_children_closedFalse, so its original exit status is unknown (null), not invented0. Separate actual outer Root89255 closes all owned processes normally: parentexit0, timeoutfalse, elapsed507.777s and normalSIGTERM, closure SHA c2cc3c489a639fb269c34f4dae2f31c01181a078dbfb4f2e87ab14122ab85b2c. That outer closure does not rewrite the worker wait flag or establish reader acceptance. Forward-control original exits255 and is normally reaped. New application operations0/configuration Applyfalse; no key replay. UX-02 remains in_progress.",
    "profile": "Actual native0.2.66 source5d1fbe6e, headed stock Firefox157 with genuine local Orca/AT-SPI/speech/PCM; partial actual navigation only, no full reader/accessibility claim",
    "source_sha256": "5d1fbe6e22511f0dec14c31adc87b30d4d1cab02bdedeb08d334e88372289607"
  },
  {
    "artifact_sha256": "f03688a1d4ffde2c83b5f516705d19443bfb83813ce7285a56032e9c1eababb3",
    "command": "Root-owned actual seven-surface Playwright UI navigation with Orca listening/log and PCM in /var/tmp/web-020-actual-reader-meyymo95; original worker exit remains unqualified",
    "evidence_locator": "/var/tmp/web-020-actual-reader-meyymo95/actual-app-reader-REPORT.json",
    "exit_status": null,
    "layer": "functional",
    "node_ids": [
      "/var/tmp/web-020-actual-reader-meyymo95/actual-app-reader-REPORT.json"
    ],
    "observed_assertion": "Original28544B raw capture reports passedtrue for7 actual DOM/speech/PCM broad rows: Library/table/model, README/source, integer alert, dialog and expanded recovery controls are actually reached with genuine speech/nonzero PCM;0POSTs/pageerrors. This does not prove status-error announcement semantics or require every expanded warning paragraph to speak automatically. Original worker reapedFalse remainsfalse and original worker exit is unknown/null. Separate outer owned closure11f674689ba922d9f40b6bd0da444ad085c98e0e9783329c27b2c9b28eae6318 is normal in75.026s; it does not replace that worker wait flag. Subsequent natural status-only observation reveals a concrete missing import-error announcement, so UX-02 remains incomplete.",
    "profile": "Actual installed native0.2.66 via real trusted HTTPS/Basic in headed stock Firefox157; genuine local Orca/AT-SPI speech log and nonzero PCM, original5d1 application before rejected-handle alert fix",
    "source_sha256": "5d1fbe6e22511f0dec14c31adc87b30d4d1cab02bdedeb08d334e88372289607"
  }
]
```

The changed-source full gate2 retained its exit1:9038 tests passed,52 deselected
in1114.68s; only `test_web_plan.py::test_acceptance_evidence_has_every_owned_case_and_planned_layer`
failed because these two unknown exits had been placed in the strict integer-only
execution list. Application tests passed; the metadata correction moves these
observations here without changing raw evidence or completed row status. The
existing entire `tests/unit/test_web_plan.py` passes9tests in0.41s after this
metadata correction. Required full gate3 must pass separately before the commit.

### Retained earlier checkpoints

Race11 actual attempt1 subsequently closes failed/unknown in129.951s, before
any browser test case. Raw `46505372…` records FileNotFoundError during initial
Chromium old51 helper startup; completion01 is false. Browser original CID exits1
normally with PID0 and complete EOF, while the separate native helper start/wait
original PID16887/start1664798 has no qualified exit or ready-process record.
The149 ordinary owned commands are reaped, but native-profile/normal-role closure
remain unqualified. No API/worker owned-role history or successful race exists;
no restoration/completion is inferred. Preserve all original handles, journals,
current prepared phase and failed flags. A bounded read-only capture of the exact
helper startup files, current identity/unit state and failure publication is being
prepared. No start, stop, signal, replay or further cohort follows from observation.

Actual initial native preparation7 now passes (`fc09e327…`,43894B). Read-only
qualification of all14 original sealed inputs, setup/draft/install/provision/
profile and final readback all complete with original transports reaped0;
cleanup_unknown is false. Current selects supported native0.2.63, application
roles remain stopped and all prior objects/calendars are retained. The original
preparation6 failure stays unchanged. No positive workflow acceptance is donated.

Actual initial63 context and official51/63 pairs now bind race11 in new0600
document `ddd65682…`; local binding provenance `3903ff50…` rejoins original
readback bytes and preserves the partial NULL draft. Root source review
`15bb2737…` and nine-flag/three-context activation `77ff51e1…` pass without
any guest action. Protected race11 stage/import then pass in13.252s: manifest
`df0ac983…`, original import `458d6657…`, all five transport phases reaped0,
no role or selector changes. Actual attempt1 now runs the genuine native51A to
63A to63B cohorts; no race, restoration or completion outcome is inferred early.
Post-race positive consumer host-full9 normalization and exactpost5 zoom consumer
are source-only preparation; one shared900-second zoom/reader hold remains required.

2026-10-28 subsequent actual WebKit8 scoped completion: corrected fixture setup
awaits all four original Library facet responses/bodies before its existing full
navigation, with no added request/retry/warm-up or deadline change. Stage/import
pass (`68047680…`, import `77977d05…`). Actual one-attempt case closes69.565s
with CJK byte/stock UI refusal passed,0 unfiltered SDK PageErrors/CSP/dialogs,
all4 original facet bodies finished and normal original closure. Raw `5b9185d9…`,
report `448a348b…` and wrapper `ff679934…` remain false: only the added passive
Window diagnostic's fourth Document exceeds its unchanged3-document cap. Actual
source identifies axe-core4.14.0 finishRun's auxiliary context.newPage; original
main about:blank/Library/detail already occupied3 identities. No auxiliary Window
event absence is qualified, and no false flag or diagnostic limit is rewritten.

Separate Root qualification `14442103…` accepts exactly the original WebKit CJK
functional/error/resource/preservation predicates after independent read-only
source/actual evidence review. The genuine3997-file response is200 and9138693B
in the independent server oracle; canonical client refuses at8MiB and stock UI
shows refusal without fallback. Browser-consumed bytes/hash remain unmeasured.
Both post-inspections/seven byte/scoped-metadata joins pass, retaining the mounted
runtime ctime delta and all-full9 false. All original roles/fetches close normally;
fresh `5ee44b98…` passes current49/BOOT/base5/Enforcing/noNFS/quiet and quiet is
released (`d9ff46ba…`). This supplies no scan10/other-engine/p95/native-profile
claim. No further run is required for these original CJK predicates; unused9
fixture drafts remain disabled and unexecuted.

Corrected native wrapper7 is locally enabled (`2eb510a8…`, active `63d1f793…`):
read-only qualification of all14 existing original seals replaces repeated
upload/seal, the exact parent/source graph remains unchanged, and setup uses the
verified official63 Python environment. Actual initial preparation7 is now running
with its five original phases/readback; no early PREPARED/workflow pass is inferred.
The genuine race11 binder, source review and final six-case merge checklist are
ready. Native/races/positive/rootless/zoom/reader and final checks/docs/commit remain.

Initial preparation6 subsequently stops at setup's first application import:
`ModuleNotFoundError: No module named hfcache`. The wrapper selected system
Python instead of the verified native63 environment. Its first three transport
phases complete0 and setup exits1; all four host originals are reaped. The
original false/cleanup_unknown result remains preserved. The failure precedes
credentials read, WORK creation and selection. Independent bounded read-only
qualification `6b37d4b3…` passes current49/BOOT/base5/Enforcing/noNFS/quiet and
proves `/opt/hfcache-web020-host-source9/runtime` absent, with all its own
originals normally closed. A distinct wrapper successor corrects the interpreter
and uses new input/upload/evidence namespaces; no original invocation is replayed.
No native preparation/workflow acceptance is inferred.

2026-10-28 subsequent single WebKit diagnostic7: stage/import pass with all
five original phases reaped0 (`41fc27bd…`, import `87584636…`). The original
one-case diagnostic closes failed/known in65.731s: raw `292edbe8…`, wrapper
`95a4f59c…`, report `f5ae5912…`. Its CJK typed client-byte refusal case passes,
but the unchanged strict browser-error assertion fails on two Library facet
requests, quantization_method and quantization, reporting access-control checks.
The full public SDK messages/stacks are now retained; observed request failures
include cancelled facet/manifest requests around navigation. That timing alone
does not prove cause. Passive document delivery reports an explicit observation
gap, so no absence-of-page-errors or aggregate acceptance is inferred. Both
archive/config inspections and seven byte/scoped-metadata comparisons complete;
all-original-full9 remains false with the measured mounted runtime ctime delta.
All originals and artifact fetches close normally, cleanup_unknown is false.
Fresh audit `d8492d2e…` passes current49/BOOT/base5/Enforcing/noNFS/quiet, and
WK7 quiet is explicitly released (`60a6d4c0…`), preserving its held original.
The failed result remains unchanged while source diagnosis proceeds in parallel.

The actual initial native63 five-phase preparation is now running, following
Root concrete effect review `b7884adb…` and the already-bound `772b3d30…` inputs.
Its scoped current49-to63 selection is authorized only in the owned isolated
guest; roles stay stopped, previous objects/calendars are retained and Enforcing
hardening remains required. No PREPARED/readback, native race or workflow pass
is inferred before original phase completion. Remaining actual acceptance,
final evidence/docs/checks and the single WEB-020 commit stay open.

2026-10-28 subsequent actual negative qualification and target staging:
Negative6 original `648f1464…` remains failed/known after its newly added full9
assertion. Both actual modified-Firefox browser profiles and both archive/config
inspections pass, with0POST/all307 original commands reaped0/normal role closure.
Separate actual read-only capture `c6cfda5f…` rejoins all seven persisted before
rows: all SHA/bytes match; five full9 rows match; only the two original runtime
ctimes differ, with the remaining eight stat fields exact. Original successful
`:rw,z` SDK mount intents are independently rejoined (`50822079…`). Prior labels
and a causal label transition were not measured. Scoped qualification
`535fcda6…` accepts the original two Firefox cases and byte/ownership/security
predicates while explicitly preserving both metadata differences and every false
aggregate flag; it supplies no WebKit qualification or blanket ctime waiver.
Fresh closure `aa1ee1cc…` passes; the two read-only observers close normally and
negative quiet is released. No further Firefox rerun is required for these facts.

Data-only legacy transfer2 now passes (`1eef1c85…`), separating actual protected
bootstrap copies from required later canonical references. Actual native63
and native51 target-only staging then pass (`8c6ff72e…`, `c16c3051…`): each has
119 verified wheel files/seven UI files, a Root-created private environment and
official native_layout qualification. Both actual target records carry the same
three GET-closure map. Combined record `25097e5f…` retains current49 unchanged,
with no role, archive, selected-profile or policy-grant change. Initial63
preparation is locally bound (`772b3d30…`) to the actual target/three closures and
13-source graph; its pure preflight passes. It has not executed or selected63.
The richer one-case WebKit diagnostic must run before changing current49.
Native race11 source and local binder finite checks pass but actual preparation,
races/positive/rootless/zoom/reader and final work remain open.

2026-10-28 subsequent actual Transport6 completion: all12 cases (four per engine)
pass in585.171s, including the explicitly modified Firefox fixture. Wrapper
`e074d382…`, original `e5f6bb88…` and report `13c40481…` retain0POST and normal
original process closure. Fresh audit `6376f3b6…` independently passes exact
current49/currentBOOT/base5/Enforcing/noNFS/quiet; transport quiet is released.
This closes fresh affected transport acceptance, with no borrowed browser or API
identity. Negative5 stays failed/known; its unpersisted before-facts cannot be
recovered into acceptance. The new two-profile Firefox collector persists all
seven original file baselines; a separate single-WebKit CJK diagnostic preserves
strict error failure while collecting previously lost error details. Neither
has run. Native race11 source is complete but still awaiting finite validation
and whole-graph freeze; all remaining actual native/rootless/zoom/reader scope
and the WEB-020 commit remain required.

2026-10-28 later Negative5/Transport6 checkpoint: negative5 original attempt1
closes failed/known in147.025s (`7b504f0c…`, wrapper `4187bb3b…`). Both expected
refusal cases pass in all three engines; WebKit's CJK browser nonetheless fails
on two lossy `Fetch API cannot load https` page-error names. The SDK maps native
JavaScript-source error console messages to pageerror, and the collector drops
URL/detail/stack; exact cause remains unresolved. No cancellation waiver or
aggregate acceptance is inferred. Final archive/configuration inspection and
raw server/runtime/Caddy comparisons are skipped by that assertion; some before
facts existed only in memory, so later reads cannot reconstruct complete proof.
Originals close normally with0POST and cleanup_unknown false; fresh audit
`a2e49f00…` passes and negative quiet is released. A fresh disabled Firefox-only
two-profile collector is being prepared with persistent before-facts, retaining
the original failed run and historical unchanged Chromium/WebKit evidence.

Transport6 stages/imports normally (`c77ad4fa…` manifest; `5db543fe…` import),
with all five original staging phases reaped and no unknown cleanup. Its actual
attempt1 now runs under a new whole-target quiet reservation. No result is
inferred early. Source-only native producer/domain and rootless consumer checks
pass; genuine native race/profile integration and remaining actual acceptance
stay open. All Source9 application/artifact/gate identities are unchanged.

2026-10-28 subsequent actual Core4 completion: Firefox-only attempt2 passes in
1375.871s. Original `3071be5f…`, report `16d64586…` and wrapper `e9b5be6b…`
retain13 passed cases,20 loads at1.801554935s p95,100 genuine same-Document SPA
cycles,30AX scans and0POST. The actual first native bootstrap body completes
before sample2's timer/navigation; no request/retry/warm-up is added. Browser,
display, container, API/Caddy, host transport and all five artifact fetches close
normally; cleanup_unknown is false. Fresh audit `671683d0…` independently passes
current49/currentBOOT/base5/Enforcing/noNFS/quiet; QUIETv4 is explicitly released.
This qualifies the modified Firefox core scope beside unchanged historical
Source9 Chromium/WebKit core2; failed Core3 remains failed/known. Negative5's
single host-proof filename collision is fixed in a separate source successor
(`84ff9c25…`), with42-row/seven-flag preview and syntax passing; negative5 and
transport6 local activations pass, while their actual cohorts remain unrun.

2026-10-28 later Core4 execution checkpoint: Source9/gate7 and runtime artifacts
remain unchanged. Core3 original `e232e73b…` is failed/known with normal closure:
Chromium completes13 cases,20 samples at1.966s p95,100SPA and30AX, then the
collector cannot read its first bootstrap response body after navigation.
Firefox/WebKit never start in that original. Fresh closure audit `12f72956…`
passes and QUIETv3 is released. No failed outcome is relabelled.

Core4 source packet `15860331…` retains the actual first native body promise and
awaits it before sample2's cache observation/timer/navigation, within the existing
case deadline. It adds no request/warm-up/retry. Root review and five-flag local
activation `c36a8dce…` pass; protected stage `77d7abe1…` and import `8bae0ed6…`
pass. Actual Firefox-only attempt2 is live under whole-target QUIETv4 with all
three agents light-source-only. The first invocation refuses locally before SSH
because Root output filenames used its reserved attempt prefix; original logs
are retained separately. The13cases/20samples/2s p95/100SPA/30AX and original caps
remain unchanged. Historical accepted Source9 Chromium/WebKit core2 results are
separate; stock Firefox does not qualify the modified Firefox fixture. No fresh
core acceptance is inferred before actual completion and normal closure.

Latest execution checkpoint (2026-10-28): Source9/gate7 and native63/
rootless64 artifacts remain unchanged. Core, negative and transport read scopes
pass across all three engines. Native27 invocation22 now passes the inert native
prerequisite (`a60f1930…`) in24.777s: Chromium, the explicitly modified Firefox
automation fixture and WebKit produce genuine trusted
hidden/visible transitions on the same retained Documents, with zero application
requests/POSTs or credential reads. WebKit's ten original input helpers close
normally with34 acknowledged key events, five Tab steps, five chords and no
pointer events; pending/unknown are false. All25 guest originals and the host
SSH close normally, and current49/base5 remain unchanged. This is capability
evidence; application/race/performance/zoom/reader acceptance is not inferred.

The retained Native26 cleanup required two one-time requests, first to its exact
MiniBrowser, then its exact private Xvfb; observation races preserve both
retirement results as false/unknown. A separate read-only completion (`a01d9537…`,
independently `fecab5bd…`) proves all nine original process identities absent,
no remaining namespace members, container exited with its actual status1,
26 original data files unchanged and fresh guest quiet. No request is replayed
and no earlier result is rewritten. The consumed-mask and pre-READY latch fixes
are now demonstrated by the fresh successful probe. The verified mechanism is
being integrated into a new disabled prefixed-race graph, retaining the existing
bounds and ownership guards. Prefixed races, positive native/rootless, genuine
zoom/reader, affected Firefox performance and final documentation remain open.
Staging generation7 completes its preparative actions but fails the final
observer-inventory publication because the pinned writer expects a bare record
name. Its original failed phase remains preserved. Fresh read-only observation
(`b4213546…`, independently `9c52642b…`) finds ten normally reaped guard queries,
an empty upload directory and the exact sealed public authorization; no input
upload or application run follows that attempt. Generation8 corrects only that
writer argument and uses fresh namespaces. Its five staging phases and confined
import now close normally in12.050s, with31 regular input members and unchanged
bounds. Its one actual cohort stops at browser-container CREATE125 before any race
phase: the unprivileged launcher cannot traverse the root-private ancestor of
`browser-private`. The136-byte original error is captured unchanged
(`6fe3d230…`); all83 original commands are reaped, but the original result stays
false/unknown (`b87b7130…`) because partial creation was unqualified. A separate
read-only lookup (`8bc7105b…`, independently `82e1867f…`) finds no object by either
exact name or case label, no CID/attach-intent files, and a fresh unchanged
current49/base5 with owned units/ports quiet. No cleanup or replay occurs.
Generation9 places the restricted runtime handoff in a dedicated root-owned
data tree, retaining private0700 directories, runtime0640/leaf0750, read-only
binding and the same-inode proof update before the existing private stdin frame.
Its prepare-upload, upload and seal originals are reaped0. Confined import
reaches its120-second timeout; completion remains unqualified and the original
host transport has no known exit status. Later PID absence does not establish
an exit or guest closure. The separate read-only observer also fails
(`c2ee39a0…`): its own SSH is reaped255 after a banner-exchange timeout, with
zero stdout. Independent local qualification (`cb3b2ea2…`) confirms that this
supplies no guest-state facts. All original failed/unknown records are retained.

The host root filesystem was separately found full with about2.1MB free while
the original QEMU process remained alive. Twelve audited, unused generated
virtualenvs are now retained on the separate /home filesystem, with complete
byte/type/mode/ownership/mtime/symlink verification and original paths preserved
through symlinks. This recovers about1.8GB; Source9, disks and original evidence
are unchanged. Fullness is an observed host problem, not a proved cause of the
timeouts. A fresh bounded observer after space recovery again closes its own
SSH with255 and no guest output (`d6a2e0f7…`). The authorized disposable-guest
recovery then sends one SIGTERM to the exact original QEMU process, confirms
its absence and no remaining disk holders, and boots a fresh writable overlay
on /home backed by the retained original disk. Both original backing files are
verified open read-only in the new QEMU; sandbox, hardware, restricted network
and seed are unchanged. QEMU reports running. No old guest-process or import
exit status is inferred. The old boot guard remains unchanged and invalid for
current proof. Fresh observation must qualify the new guest boot, identities,
confinement, artifacts, original import state and quiet before further acceptance.
The subsequent owned post-boot inventory passes (`6c34c7bc…`): current49,
fixture/control bytes, Enforcing/noNFS, five newly discovered process identities,
inactive application roles/timers and quiet ports are rejoined. All ten guest
queries and the host SSH close normally. A separate fresh guard is installed
and verified (`acae12a1…`), preserving the old guard and every prior record.
The read-only import observer (`56c20f91…`) finds saved CREATE0, an empty
persisted CID, attach intent/process records and no final result/import proof.
Two further exact name/label lookups close normally (`85e5d7eb…`) and identify
the same retained container in Created state. Old process identities are absent
in the new boot; their exit statuses remain unknown. No cleanup, import replay
or application acceptance is inferred. Fresh disabled acceptance copies are
being rebound to the new guard without changing product inputs or budgets.
Generation10's five staging phases and confined import then pass in25.966s;
the import's four originals and container close normally with0. Its actual
cohort (`f81f0811…`, report `b5aaa94f…`) fails with known normal closure in
240.589s. Chromium's initial phase passes, but the first read-only Doctor POST
returns503/HFAPI022 and no operation receipt is admitted. The original browser
record remains uncertain and no request is replayed. The fixture reuses the
read-only WEB013 server configuration, which omits the protected host helper;
Basic Doctor admission correctly requires fresh Hub authority. Genuine fixture
authority provisioning and its dependency on canonical host preparation are
now addressed by the dated sequencing amendment below. No HostStatus mock,
admission bypass or grant relaxation is an accepted correction. All failed
evidence and synthetic fixtures remain retained.
Prefixed races, native/rootless positive workflows,
genuine zoom/reader, affected Firefox performance and final documentation/checks
remain open. Stock Firefox native/performance acceptance is not established by
the modified-fixture prerequisite.

2026-10-28 fixture sequencing amendment (Root decision; no execution): the three
completed current49 GET scopes and their original normal closures remain
pre-canonical evidence. The fourth, prefixed race scope remains mandatory and
open, but moves after canonical staging and genuine protected fixture
provisioning. The previous four-before-canonical requirement was an agent
fixture ordering assumption. Basic read-only Doctor requires fresh Hub
authority on both request admission and execution; removing that check or
substituting a status object is not a correction. New source-only producer
contract-v5 records the three pre-canonical names separately from the required
post-provisioned scope; it does not change any frozen executable gate.

The concrete reuse sequence for source review is:

1. Qualify official native51 and native63 targets against their own immutable
   source, wheel and UI artifacts. The old51 survey (`f22b6858…`) proves the
   read-runtime prefix and its bytes, not an official native profile. Its
   `e58932f1…` source and `4c194a19…` UI remain distinct from Source9's
   `776470cc…` source and `f172aad2…` UI. If51 lacks a qualified canonical
   target, use a fresh guarded copy of the existing official staging recipe;
   do not relabel the runtime prefix or overwrite an unexplained existing tree.
2. Reuse the WEB019/positive private `/etc/hfcache` and `/srv/hfcache` mounts,
   fixed hfcache UID/GID, actual indexed API/helper peer and protected protocol.
   Provision only Hub permission for the race, with each synthetic archive ID
   and version-matched deployment independently bound. Every engine begins on
   real51, then switches to63 on archive A and63 on archive B. The continuous
   Caddy/origin, owned browser, original Documents, operation receipts and
   pending handles survive the intended phase transitions.
3. After the original Doctor has a qualified terminal record, drain only its
   API/worker/helper phase through retained PID/start, invocation, cgroup,
   transport and socket proofs before changing profile or protected authority.
   A separately reviewed phase drain may retain a known owned browser and
   Caddy; it must not call the full positive controller stop or fabricate its
   browser-closed prerequisite. Any unknown blocks dependent actions. Final
   teardown retains the existing known-browser-closure gate and complete
   original-role/endpoint/input checks.
4. Run the unchanged nine race cases, three original Basic Doctor POSTs,
   fifteen phases and six synthetic archives across all three engines. Preserve
   native same-context gates, no-replay behavior and all original clocks/caps.
   The fourth scope passes only from its own actual results and normal closure.
   Native/rootless positive acceptance, the separate900-second zoom/reader
   handoff, affected Firefox performance and final checks remain required.

The source workflow and authority records are drafts until Root reviews the
concrete new generation. Current canonical51/63 qualification, profile
preparation, prefixed success, positive execution and private handoff facts stay
unbound. This sequencing decision authorizes no guest action by itself.

The116 previously deferred local workflow/zoom/reader models, focused lint,
syntax and disabled previews pass (`12dd727c…`); all28 local direct children
are reaped and47 frozen source inputs remain unchanged. These source checks do
not supply application, zoom, speech or screen-reader acceptance. The human-guide
label/keyboard/large-library review finds no concrete mismatch against Source9.
Detailed evidence and preserved earlier checkpoints follow.

Latest checkpoint (2026-10-27): source6 installed native57 cohort10 closes
normally in372.787s with zero POST attempts, unchanged archive/configuration and
`cleanup_unknown=false`. All20 Chromium initial samples complete; median is
1.763754s and nearest-rank p95 is2.844419s, above the unchanged2s target. The
19 warm documents have actual zero-transfer asset cache evidence. Connected
keyboard workflows and29 accessibility scans pass; the3997-file manifest renders
and its keyboard jump reaches file3251. The next scan finds12 serious accessible
name mismatches: visible `Inspect metadata` is not contiguous in the button's
old accessible name. The correction uses `Inspect metadata for file N`, retains
the path in the row header and selected evidence, updates ADR145/human guidance,
and passes all8 virtualization component tests. Built-browser revalidation remains
required. Original result `50eb0531…` and diagnostic join
`source6-installed-load-and-label.json` (`818b6aed…`) remain preserved.

Source6's matching strict gate4 passes9030 backend/4029 combined web tests in
1541.606s, with no changed inputs or required skips. Its initial JavaScript
closure is204,899 gzip bytes, below358,400. The accessible-name correction is
newer than that source snapshot: final freeze, artifacts and matching gate are
still required. A fresh-byte parser partition experiment shows no improvement
and is not adopted. Other path-opening optimizations remain measured proposals,
not accepted behavior. Source-only zoom/reader/rootless/race coordinators do not
close any installed acceptance row. All-engine load/SPA retention, actual native
and rootless positive workflows, real transitions, zoom, reader and installed
slow/cancelled/stale transport cases remain open.

Source7 now freezes1528 inputs at
`2389af4f1e7b38f23374e1d388355c4277d4ad36558b1661e7103dc780823ba3`.
Its four changes from source6 are the metadata action name, existing component
assertions, ADR145 and the human keyboard guide. Python and wire source pins are
unchanged; the parser partition, pure-path and kernel-opening proposals remain
unadopted. Native59 stock wheel/UI/image and pinned-foundation build pass with
canonical source unchanged. Matching rootless60 stock build and both actual
no-runtime-Node probes also pass; complete JavaScript gzip inventories are
254,308/254,306 bytes. Fresh59 prefix installation verifies119 wheel leaves,
followed by frozen public helpers and the actual confined diagnostic-module
import preflight. These start no application role and change no selector.
Strict matching gate5 now passes0 in1522.413s with unchanged1528 inputs:9030
backend tests (52 opt-in deselections),4029 combined web tests, wheel profiles,
Cockpit, production build, startup browser and real-API read fixture. Installed59
cohort11 is running against these exact artifacts to recheck the accessibility
correction and remaining browser matrix. No new p95 or installed pass is inferred
until actual evidence exists; cohort10's false result remains unchanged.

A passive audit of the original live cohort11 now joins its exact runner,
descriptor, API and Caddy identities and observes all20 Chromium load samples
with20 completed enrichment observations. Nearest-rank p95 is1.792672248s,
meeting2s; the cold sample is2.981s and all19 warm samples are1.656–1.793s.
The actual initial-load case records completion/pass. Connected accessibility
checks are in progress, with Firefox/WebKit not yet started at this checkpoint.
This is partial live evidence (`functional11-passive1.stdout`), not final browser
matrix or normal-closure acceptance. Heavy concurrent testing remains held
through the full cohort to keep later-engine measurements isolated.

Later passive audits2–4 confirm the same original runner/API/Caddy/descriptor.
Chromium now completes all13 cases, including100 genuine same-document
route/refresh cycles, the large-manifest window and30 accessibility scans.
Firefox completes its20-sample load/enrichment case at1.874439061s p95, plus
connected accessibility and the large manifest (30 scans); its first50SPA cycles
complete while the next chunk is in progress. WebKit has not yet started at that
audit. These remain partial original-cohort observations; final result, all-engine
matrix and original normal closure are still required. Actual audits remain in
`functional11-passive2/3/4.stdout` without changing the original collector.

Passive audit5 again verifies the same original roles and descriptor. Firefox
now completes all13 cases/100SPA cycles, matching Chromium; each engine has30
accessibility scans. WebKit completes20 initial load/enrichment observations at
1.953211120s nearest-rank p95, meeting the unchanged2s target, and passes connected
keyboard/accessibility, the large-manifest case and30SPA cycles. Its next cycle
chunk is in progress. The actual evidence is `functional11-passive5.stdout`;
this remains partial live evidence until every case and original normal closure
are joined. The quiet timing lane remains held through the complete cohort.

Cohort11 now terminates with original `passed=false` and browser exit1. Its
normal API/Caddy closure and `cleanup_unknown=false` are independently joined to
a fresh unchanged five-process quiet baseline. The9,402,147-byte report exceeds
the original8MiB collector/retrieval artifact cap. A separate read-only retrieval
uses its exact observed size, full identity and SHA256 `7dfac9c5…`, preserving
both failed collectors. That report verifies Chromium/Firefox's13 cases and100
SPA cycles each; all3 engines complete20 load samples at1.793/1.874/1.953s p95,
the connected/large-manifest cases and30 accessibility scans each. No product
budget failure or POST is recorded. WebKit stops at95 cycles on a1ms strict
`performance.timeOrigin` equality failure, while the retained actual Document
reference, immutable marker, navigation entry and zero navigation/load-event
fences still match. This is consistent with [WebKit's documented drift
issue](https://bugs.webkit.org/show_bug.cgi?id=258572); it does not establish
100 WebKit cycles. A new targeted whole100-cycle collector must retain every
actual Document/navigation fence and report the unstable WebKit timestamp as
diagnostic evidence. No original result or product threshold is changed.

The matching gate5 read-fixture join now passes (`0552649a…`): root and prefix
each complete8 cases/100 cycles with maximum2 active/1 waiting reads and
25,178,112 reserved encoded bytes below33,554,432, completed service headers,
cancellation/stale fencing and final drains. Actual cohort11 initial JavaScript
requests join the exact source7 stock manifest at204,905 gzip bytes in each of
the3 engines, below358,400; the README chunk is absent. These narrow joins do
not turn the original failed browser cohort into complete matrix acceptance.

Independent audit `212937d8…` rejoins cohort11's raw evidence and finds incomplete
checks that its summary must preserve: each engine has one critical popup-IDREF
incomplete, ten serious prohibited-name incompletes and29 serious contrast
incompletes. Zero serious/critical violations does not mean these checks are
resolved. The pinned axe4.14 source identifies popup controls as a manual-review
branch; actual same-document listbox, label and active-option IDs still need
focused verification. The prohibited-name targets map to intentionally labelled
generic containers: sanitized README source, selected job effects and host
controls. Give these existing labels explicit supported group semantics, with
focused accessible-role/name regressions and ADR145/human guidance amendments.
This is a source8 correction; source7's immutable artifacts and actual running
targeted WebKit100-cycle cohort remain historical evidence. Final acceptance
requires new source8 artifacts, matching gate and browser evidence. No source7
result is rewritten or silently promoted to final-source acceptance.

Source8 freezes1528 inputs at
`32e7f0b76491b192361f9b78179a2553519e12cd9b8e3c57a72b82bc8f2fc278`.
Its eight differences from source7 are three named-group roles, three existing
component regressions and ADR145/human guidance. The red baseline has exactly
three missing-group failures; all59 focused component cases then pass, alongside
scoped lint/format checks (`source8-semantic-groups-v1/RESULT.json`, `aa80f41d…`).
Backend/wire bytes and dependencies are unchanged. Matching native61 stock build
passes72.707s, with source proof `9556eda3…`, UI manifest `6893377b…` and pinned
UBI10micro foundation. Rootless62's first build remains false: its retaining
wrapper inherited umask077, producing a0700 Python parent directory in the image
that its unprivileged runtime could not enter. Exact stopped-container/mode and
read-only ancestry evidence remain preserved. A fresh work/tag with explicit
umask022 passes55.289s, source proof `bddb203b…` and UI manifest `7d6769e7…`;
the failed image and outputs are untouched. Both actual new images pass isolated
no-runtime-Node/package-manager probes, retaining stopped containers, and each
complete JavaScript inventory is254,330 gzip bytes. Matching gate6 is running;
source8 installed/browser acceptance remains required.

Source8's matching gate6 now passes0 in1508.707s on unchanged1528 inputs:9030
backend tests (52 opt-in deselections),3702 web unit/4029 combined frontend,
95% line/90.01% branch coverage, required Cockpit/build/wheel/startup and actual
HTTP read-fixture checks. The matching read-fixture join (`12e835a7…`) verifies
root/prefix8 cases and100 cycles each, maximum2 active/1 waiting reads and
25,178,112 reserved encoded bytes below33,554,432, completed service headers,
cancellation/stale fencing and final drains. It remains separate from installed
Caddy/Basic acceptance. The canonical whole-repository source digest32e7f0b7
and actual compiled frontend source digest79ce33c8 have different scopes;
`source8-artifact-bindings-v1.json` (`91c5da88…`) joins both actual stock artifacts
and their UI manifests. Bootstrap comparisons use the compiled frontend digest.

The new native61 prefix's original stage exits1 after root-owned offline/no-cache
installation and checks of119 package leaves/7 UI files. Its final permission
predicate refuses only the newly created empty UV environment lock at0666.
A read-only5319-entry audit finds no other writable entry and all owners are
root; original application roles remain inactive and the selector stays49.
No installer or failed record is replayed. A separate scoped completion must
hold that existing noncode lock nonblockingly, preserve its inode while changing
only its mode to0600, rejoin every code/asset/input and original failure, then
perform the remaining readability/TLS/receipt steps. The old failed stage stays
false; no prefix-install or browser pass is inferred before actual completion.

The source7 targeted whole100-cycle WebKit original now closes normally but
remains false (`10c41fe3…`). It completes83 cycles, then a15s public Library
settlement predicate times out while facet enrichment is still pending. The
retained actual Document/navigation fences match; this failure is separate from
cohort11's timestamp drift. No timeout cause or100-cycle pass is inferred.
Original archive/configuration remain unchanged across5314 files, zero POSTs
are attempted, and a fresh read-only closure join (`49ab2668…`) confirms all
original roles gone and the unchanged quiet baseline. Host gate/build work
overlapped this historical target; it does not establish the failure's cause.
Source8's collector must retain named wait phases and actual outstanding-read
diagnostics, full bounded incomplete-check data and popup ID-reference proof.

Canonical native59 staging installs the candidate and verifies119 package source
leaves, then exits1 when its final full-prefix classifier correctly refuses the
currently selected rootless49 layout. The original9.4s failed result
`adddbf58…` remains unchanged; staging is not replayed. A separate2.511s read-only
qualification (`e5e1559a…`) uses the official target-only native classifier and
verifies1534 source records/modes, native payload,119 wheel leaves,7 UI files and
protected ancestry. It confirms unchanged rootless49 selector/full metadata and
quiet roles. The original `stage.json` completion record is absent. Later helper
preparation must explicitly bind this separate qualification and preserve the
failed original; no installed workflow or native selection is inferred.

Current checkpoint (2026-10-27): WEB-020 remains in progress and uncommitted.
Source4 freezes1526 inputs at
`a1e96d05f1fcc75e50ed7fe7cf2f4d0aefbf2da02472f41b699748aa5550c8b2`.
The measured catalog optimization now validates present observations through
their existing authoritative reader once, still binds missing observations, and
uses equivalent lexical containment fast paths before the unchanged no-follow
descriptor walk. Actual guest warm domain reads improve from1.407/1.375s to1.047s
with identical full payload SHA256; this does not establish browser p95.
The240 focused authority/path/concurrency regressions (26 new cases),155
wire/API/MCP tests, lint, types, wire generation and documentation alignment pass.
Public definitions/routes/result shapes/schema remain unchanged; reviewed
metadata/path pins and three publication context pins produce wire digest
`bbe6f95d5468286151250c93d1c33ed27d52eee4a4828407503df9b268222701`.

Matching disposable native53 and rootless54 stock builds, source proofs and
pinned UBI10micro foundation checks pass. UI manifests are `0cd42794…`/`f9134b32…`;
wheels `95b37f54…`/`ecd48423…`; shared images `30231197…`/`3c3d78da…`.
Both actual images have no runtime Node/npm/pnpm. The native probe's first
collector result remains false because the inspector omits the image's SHA
prefix; separate read-only qualification joins its exact stopped container,
zero exit and original logs without a rerun. Gzip JavaScript totals are
254,307/254,310 bytes. Actual installed native53 initial Chromium requests join
the exact stock manifest at 204,904 gzip bytes, below the 358,400-byte ceiling;
the README chunk is absent from that initial closure. This narrow byte-budget
pass does not establish load or browser-matrix acceptance.

Strict matching source4 gate3 passes0 in1511.642s with no changed source files:
8978 backend tests (52 opt-in deselections),3702 unit/4029 combined web tests
with no required skips,95% line/90.01% branch coverage, wheel profiles, Cockpit,
production build, startup browser and real-API React read fixture. Its actual
root/prefix integration reports join in `gate3/read-integration-source4.json`
(`e3e0974c…`):8 cases each, zero skips/retries,100 cycles each, maximum2 active/
1 waiting reads,25,178,112 peak reserved encoded bytes below33,554,432, delayed
completed service responses, cancellation/stale retirement and final drains.

Installed native53 cohort7 remains false: ten initial usable samples were
collected (first3.216s; subsequent2.476–2.779s), then a45s read-settlement deadline
stopped collection. The required20-sample p95 is unestablished. The original
result `775a5d7f…` retains `cleanup_unknown=false`, normal browser/API/Caddy
closure, zero POST attempts and unchanged archive/configuration. Revision
inventory has10 requests but9 response headers; the retained service logs do not
establish whether the missing read was still running or cancelled at deadline.
No timeout cause or performance pass is inferred. New immutable collector inputs
are being prepared to retain exact request lifetime/outstanding-read diagnostics
and observe the Library's public settled state between fresh documents, while
keeping the2s product target and all original failed inputs unchanged. Positive
helper, zoom, reader, rootless and real-transition evidence is still required.

Latest installed source4 cohort8 completes all20 Chromium initial samples and
public enrichment observations without a read-settlement timeout. Nearest-rank
p95 is2.753678371s against the unchanged2s target. The next connected model
overview scan finds33 nodes with a serious color-contrast violation. The original
false result `9b45107d…` closes normally in332.29s, with browser exit0, all owned
descendants gone, API/Caddy waits0, `cleanup_unknown=false`, zero POST attempts
and unchanged archive/configuration. Summary
`source4-installed-load-and-contrast.json` (`6ed77c04…`) retains the original
report/result joins; it is not a browser-matrix pass.

The contrast fix replaces six lighter repository text colors with the existing
shared muted foreground. Its calculated contrast is4.645:1 or greater against
the four relevant backgrounds, while actual final built-browser scans remain
required. ADR145 and the human keyboard guide describe the presentation change;
INV021 review finds no new authority or invariant. This changes the source after
gate3 and requires a new freeze, artifacts and matching strict gate.

Warm resource timings also show complete JavaScript/CSS transfers on every fresh
document. The pinned Playwright1.64.1 Chromium implementation enables protocol
authentication handling for `httpCredentials` and sends
`Network.setCacheDisabled(true)`, even without user routing. The previous
collector's claimed normal-cache policy therefore needs independent correction
and actual cache evidence. An inert authenticated cache probe is being prepared;
no revised p95 pass, application optimization or target change is inferred from
the framework source alone. All original failed measurements remain retained.

Source5 freezes the contrast correction and its two documentation amendments at
`c14aa8238cf81257a249e72cd4d5133d0910067712f50020ef77a2f9c7aa3be9`
(1526 inputs); backend and wire definitions remain identical to source4.
Matching native55/rootless56 stock builds, source proofs, pinned UBI10micro
foundation and actual no-runtime-Node probes pass. Each complete JavaScript
inventory is254,306 gzip bytes; matching installed initial closure remains
pending. Native55 prefix installation passes in4.722s with119 wheel package
leaves verified, followed by the frozen public helper leaf in1.631s. Neither
starts a role or changes the existing `.49` selector. Source5's matching strict
gate and installed functional acceptance are still required.

The first inert cache probe remains false: an independent CDP session did not
restore caching. A second fresh probe uses the exact pinned SDK main-page
protocol owner, preserving credentials and automatic auth challenge handling.
It passes: three fresh authenticated documents request the immutable asset3
times under the original setting versus1 after restoring default caching; warm
resource transfers are0 with two actual cache events. Real401 negative and
native challenge/200 controls pass in both conditions. Original
`cache2-original-result.json` (`6b7977a9…`) retains normal browser/server/container
closure and fresh quiet baseline. This is an inert harness prerequisite, not an
application p95 pass. The next source5 collector is being prepared to bind this
exact proof and retain real cache observations without changing the2s target.

Installed source5 cohort9 now completes all20 Chromium samples with actual warm
asset cache evidence. Its nearest-rank p95 is2.233954866s, above the unchanged2s
target. Connected keyboard cases and29 accessibility scans have no serious or
critical findings. The subsequent large-manifest case fails; exact frozen client
and server reproduction identifies9,138,693 ASCII-escaped response bytes above
the browser's8MiB cap, despite a valid5.67MB durable manifest. Original result
`67235386…` retains normal closure, no unknown cleanup, zero POST attempts and
unchanged archive/configuration. No later-engine or large-manifest pass is inferred.

A new fixture preserves240 repositories,3997 files and1024-byte UTF-8 paths, but
mixes ASCII and Unicode prefixes so the actual escaped response is7,281,018 bytes.
The frozen client accepts it; a same-byte-length Unicode-work negative still
refuses at the existing8,000,000-work ceiling. Real ordinary-file queries and
the next-file structural refusal pass. The old oversized fixture is preserved.
The new100-cycle collector uses visible SPA navigation and refresh controls with
document/time-origin fences; the earlier full-document loop is diagnostic only.
Neither revised collector has installed acceptance yet.

Decision157 is accepted contract-first for source6: after every fresh anchored
read and all query accounting, bounded exact-byte memoization reuses only frozen
Reference and64KiB–8MiB manifest parsing. Raw keys are bounded at10MiB; all outer
authority joins remain fresh. The actual installed55 isolated query comparison
is1.000s original/0.959s cold/0.630s warm/0.981s restored, with identical full
payload and unchanged source/archive/configuration. Static implementation now
passes52 new refusal/freshness/accounting cases and136 existing catalog cases,
plus98 independent wire tests, lint, types and219-document alignment. Renewing
the reviewed storage and publication.card pins yields source digest
`11c597423b0e78efee4fa5c0b8457ad4c49251e50d9e11c8865a0369a16257e1`;
public definitions/routes/results/schema remain identical. Matching artifacts,
the strict gate, actual browser p95 and memory acceptance remain required.
AD-12/113/145 and INV018 are amended in this
work package; no endpoint, format, privilege, dependency or target is widened.

Source6 freezes1528 inputs at
`66b8b036e6d474fcdfda954b1314163f6d2992cc49e6e6b15a86c421d0e4ae2f`.
Static proof is retained in `source6-parser-review/evidence.json` (`4b82bf25…`):
the canonical52 cases pass2.33s, the proposal52 pass4.02s, and136 existing cases
pass5.86s. Native57/rootless58 stock artifact builds complete0 with unchanged
source and passing foundation checks. UI manifests are `b3e25f0f…`/`f18b0ed4…`,
wheels `40e34d6f…`/`b772fe5e…`, images `be649346…`/`179ab9ad…` and source proofs
`2c6d6254…`/`875badb7…`. Matching strict gate4 is running. No matching installed
acceptance is inferred; the earlier `.49` selector remains unchanged.

Both actual source6 image probes confirm no runtime Node/npm/pnpm and normal
stopped-container closure. Complete JavaScript inventories are254,301/254,303
gzip bytes; actual initial closure remains pending. Fresh native57 installation
passes5.525s with119 package leaves and descriptor `28505a44…`; public tools
pass1.833s with manifest `7db4631b…`. The revised v9 collector and its confined
module-import preflight pass26.08s, manifest `bf3e69bd…`, original import proof
`ff1d9bd2…`. No application/browser role or selector is started by preparation.
Its fixed mixed-Unicode fixture, actual default-cache proof and100-cycle SPA
collector are staged. Matching strict gate4 passes0 in1541.606s with all1528
source inputs unchanged:9030 backend cases (52 opt-in deselections),3702 unit/
4029 combined web cases,95% line/90.01% branch coverage, all wheel profiles,
Cockpit, strict web checks, builds, startup browser and real-API read fixture.
The matching read-fixture join `gate4/read-integration-source6.json` (`0b59c241…`)
proves8 cases at root and prefix with zero skips/retries,100 cycles each, maximum
2 active/1 waiting reads,25,178,112 reserved encoded bytes below33,554,432,
delayed completed service headers, cancellation/stale fencing and final drains.
This is separate from Caddy/Basic/installed acceptance. Installed cohort10 is now
running in the quiet timing lane; no new p95 or browser-case pass is inferred.

The owned native input prerequisite now passes9.293s: actual private seat
capability/keymap events after a public modifier, released keys/modifiers and
empty unchanged focus precede a committed public z. All40 tracked processes and
observer FDs close normally. The separate inert native Basic prerequisite passes
12.617s: real401, native readiness/typing/Tab/Return, actual200/public heading and
dialog removal, with40 owned processes closed. Input debugging stays off and the
metadata observer disconnects before private input; retained outputs contain no
credential values. Qualification `f57c24fd…` proves this prerequisite only; actual
application Orca/speech and the six required reader surfaces remain open.
Real build/archive/current transition browser acceptance is also pending. An
actual old51/new57 read-only package/assets/wire survey passes (`daf78ea0…`), and
the local current-transition model proves the application publisher/real writer
lock and refuses stale/replayed or schema-valid corrupt-current joins. Its
revised helper still requires the coordinator's guest context/mode/ownership
bindings and real installed browser execution; it is not a transition-case pass.

Reader-only1 completed false in814.032s before its900s deadline. All four owned
reader attempts, tunnels and the original API/Caddy closed normally; original
result `ff800223…` has `cleanup_unknown=false`. A separate trusted credential GET
passed200, but native AT-SPI field edits did not retain text, so no actual app
authentication, Orca utterance or reader acceptance is inferred. The native input
prerequisite is being corrected before another application run; old evidence and
the `.49` selector remain preserved.

Earlier matching source3 checkpoint:
The source3 snapshot is
`9b01098aaf8d72eef9bf542083fe1b5614d13508a7ea59eaf589f2cde0a097f5`
(1525 inputs), with disposable `.52` wheel `da4f9491…`, UI manifest
`c8fe9289…` and shared image `966df268…`. Its stock build, pinned UBI10micro
foundation, no-runtime-Node proof and exact installed wheel/assets checks pass.
The matching strict web/Cockpit gate2 passes0 in1610.169s with no changed source
files:8952 backend tests (52 opt-in deselections),3702 unit/4029 combined web
tests with no required skips,95% line/90.01% branch coverage, wheel profiles,
Cockpit, production build, startup browser and real-API React read fixture.
Its result is `gate2/strict-gate-result.json` under the evidence root. The
earlier startup pass and changed-source gate1 failure remain separate originals.
The matching gate's real-HTTP integration evidence is joined separately in
`gate2/read-integration-source3.json`:8 cases each at root and `/management`,
zero skip/retry,100 query cycles per profile, maximum2 active/1 waiting reads,
25,178,112 peak reserved encoded bytes, and stable2029/2033 settled bytes.
Actual initial Chromium script requests join the exact installed asset manifest
in `source3-initial-javascript-closure.json`:204,901 gzip bytes against358,400,
with the README chunk absent from that initial closure. That byte-budget proof
does not turn the failed installed load cohort into a p95 or matrix pass.

Installed cohort6 reached the real authenticated Library through the existing
trusted Caddy with Chromium156:25 validated rows,240 known matches and enabled
Find/Apply controls in5.561892s. That sample misses the2s target; subsequent
background enrichment exceeded the private collector's10s quiet deadline, so
no20-sample p95, later screen,100-cycle or three-engine pass is established.
All browser descendants and the original API/Caddy invocations closed normally;
the false original result `f92d4a72…` is retained with `cleanup_unknown=false`.
The actual installed query is being profiled on the guest; no budget or product
bound has been raised. Cohort5's earlier module-layout failure and all previous
failed/unknown originals also remain preserved. A new read-only public helper
leaf preserves the canonical sibling module layout and passes an actual
confined, network-disabled import preflight before any seeding/service start.

The large positive fixture retains all240 repositories and3997 files in its
largest manifest:99,988 structural tokens, below the independent100,000-token
authority limit. The next added file is refused. Original6502-file attempts
remain negative evidence; the8MiB browser byte ceiling alone did not make them
valid authority fixtures. Actual UI200% zoom, reader smoke, connected positive
helper workflows and the remaining race/memory matrix are still acceptance
work. Inert zoom/Orca prerequisite passes are explicitly preparation only.

Activated2026-10-27 after WEB-019 committed as `abaef80` with a clean tree,
strict gate0 and all42 required scoped installed browser pairs accepted. Preserve
its failed original collectors, separate qualifications, retained config inode,
SDK handles/journals and all older unknown state. Existing guest/.49 rootless,
Caddy and engines are quiet and reusable; no production effects or new engine.

Start with the demonstrated hidden-tab polling gap, actual connected-workspace
accessibility scans and declared large-data/100-cycle measurements. Keep all
existing named auth/configuration/operation/README decisions and coverage gates;
record each discovered defect with a meaningful regression. Establish an owned
real Orca/browser session for the screen-reader slice using already installed
software, without borrowing the greeter or changing user/production services.
Keyboard, zoom and axe evidence remain separate from actual reader evidence.
Review manifest virtualization against existing bounded local pagination before
implementing; retain the declared budgets and accurately name the final behavior.
No tolerance inflation, skipped required browser or false manual-acceptance claim.

Read-only preparation found the installed local Orca/speech/AT-SPI stack but no
owned graphical session; the guest host lacks that stack. Its finite owned
session startup and actual smoke remain unproved prerequisites. Task020 owns
actual outcomes, invariant/ADR amendments and human browser/keyboard/large-library
guidance. No implementation or acceptance is inferred from preparation notes.

### Resumed checkout and reboot recovery (2026-10-27)

Reconciled `abaef80` on `feat/web-ui` with the preserved dirty checkout before
work. Startup strict gate (`scripts/check.sh --require-web --require-cockpit`)
is running with retained output at
`/var/tmp/web-020-validation-nvj5zeg7/startup-gate.log`; it is a recovery run,
not yet final matching-source acceptance. Known manifest lint regressions were
fixed before further implementation. Focused virtualization components pass8/8;
web lint and both TypeScript projects exit0. No coverage exclusion or dependency
was added.

The real-HTTP read fixture now exercises the actual typed client, query store,
read coordinator and encoded-retention budget across100 handle/refresh cycles
for both root and `/management`. Both8-case profiles pass with no retry/skip:
108 started GETs, maximum2 active/1 waiting, peak25,178,112 reserved encoded
bytes below33,554,432, and stable settled samples2029/2033 bytes. Cancellation,
stale completion and auth-generation retirement, oversize and unsafe-integer
negative post-service corruption, and final browser/API/query drains pass.
This is source-built real-auth HTTP integration, separately from installed SPA,
Caddy, route churn, browser heap and NAS acceptance. Two earlier test-harness
failures (finite observation deadline and exact `unsafe_number` expectation)
remain preserved; product budgets were not increased. Evidence:
`/var/tmp/web-020-validation-nvj5zeg7/web020-integration/evidence.json`.

Recovered the same positively owned disposable disk after proving the old QEMU
and SSH listener absent. New guarded QEMU retains KVM/q35,2vCPU/4GiB, sandbox,
restricted networking and the original loopback SSH46261 endpoint. Original
control/PIDs remain historical; a fresh guard binds the actual new guest boot,
five current manager identities, fixture marker, Enforcing policy, no NFS mounts,
quiet app roles/endpoints and inactive/unenabled calendars. The `.49` selector,
old archives/stores/handles and failed evidence remain unchanged. Recovery proof:
`/var/tmp/web-020-validation-nvj5zeg7/guest-recovery-72o41awj/`.

Source1 freezes1524 inputs at
`e58932f1b86f58121320d8ed409006b8f1aa8637920611e398f3ed9da6f731c2`.
Matching disposable `.51` wheel/UI/shared image build passes with unchanged
canonical inputs. Wheel SHA256 `6667332f…`, UI manifest `4c194a19…`, image
`920c3f2d…`; the existing foundation checker proves pinned UBI10micro provenance
and confined offline/nonroot runtime. Fresh owned native prefix installation
exits0 in7.658s, checks installed wheel bytes and asset identity, and starts no
service or selector change. Stock/installation proof is under the same evidence
root (`native-artifacts/stock.json`, `runtime-stage-result.json`). These are
build/preparation results, not actual connected-browser acceptance.

The declared synthetic data has240 fictional repositories (120/type),230
configured entries and a real6,502-file manifest. Calibration preserves tiny
ordinary files:8,543,015 durable manifest bytes versus7,671,642 compact payload
bytes, below the browser8MiB ceiling. The actual generated decoder accepts it;
capture of the hostile inert README also produces a real `present` record.
Neither local calibration nor a source test substitutes for installed load proof.

The first installed cohort (`2042d5512dfb4718a902d103662f7c11`) ends false in
52.321s with known normal API/Caddy closure, browser container exited1 and no
browser REPORT. The trusted Caddy Basic challenge passed. Its private browser
driver incorrectly required host-action fields absent from the plain read-only
runtime, failing before browser cases. Original result SHA256 `6a461a83…` and
all inputs remain unchanged. A separate versioned driver removes those stale
harness guards while binding the actual native origin and report/truth owners;
no product result or acceptance is inferred from that correction.

The strengthened integration repeats successfully with both100-cycle profiles:
six completed-service delayed replies per profile, with two interruptions after
real response headers and before body delivery. All116 actual API observations,
exact protocol refusals and final ownership drains pass. Evidence is separately
retained in `web020-integration-v2/evidence.json` under the evidence root; the
earlier evidence remains intact. Three test/fixture-only changes since Source1
have explicit unchanged-runtime hash/mode comparison; final source/gate identity
must include these changes and the developer-guide updates.

Owned Orca prerequisite v9 actually speaks the inert page's input/button labels,
then closes all46 tracked identities. Earlier failed attempts remain false.
Separate real Chromium native-profile and Firefox native-menu200% zoom probes
provide mechanism evidence; application/three-engine zoom and reader smoke
remain required. No startup, axe, viewport or DPR substitute closes those rows.

Remaining: connected three-engine scans/workflows, actual helper-backed editable
configuration/dialog states, current/authority changes, slow/stale installed
reads, old-open-page contract mismatch, actual reader/200% matrix, fixed-fixture
p95/bundle/100-route-cycle retention, final coverage/strict gates and completed
human/case evidence. The read-only prefix cannot open protected editable forms;
those require the actual owned native helper fixture, not a fake helper or a
denial-only replacement. Task/current selector stay in progress until all pass.

Scoped completion-v1 now closes false with all three original transports reaped
and `cleanup_unknown=false`, before its lock claim or permission change. Its
tree model used the audit's root-inclusive5319 count as a descendant count.
Fresh root read-only audit verifies5319 total entries/5318 descendants, the
original empty root-owned lock still0666, absent runtime/installation receipts
and the unchanged five-process quiet baseline. Both failed stage/completion
records and sealed inputs remain unchanged; a new version must join this exact
audit and distinguish both count conventions before proceeding. This is a
collector correction, not installed browser acceptance.

2026-10-28: separate scoped completion-v2 passes, original result
`fd9f4bef…`, with all original transports reaped, `cleanup_unknown=false`,119
wheel files/seven UI assets verified and the version probe running as UID1000.
It joins the original false stage, false completion-v1 and exact fresh tree
audit before acquiring the existing empty noncode UV lock without creating or
blocking. Only its mode changes0666→0600; its original inode, every code byte,
selector, historical control and five-process quiet baseline are preserved.
The protected root-owned installation/`COMPLETION-v2.json` records distinguish
5319 root-inclusive entries from5318 descendants. Public helper stage-v4 also
passes (`45e53ff4…`), with fresh root-created inodes and manifest `e920ff4f…`.
No application role starts. The canonical1528 source inputs still match32e7f0b7;
the separate frontend build-source digest79ce33c8 is retained explicitly for
bootstrap identity. A new bound core collector is being finalized; these
preparation facts do not establish browser acceptance.

The frozen core-v2 collector joins the actual runtime/public facts and retains
the separate canonical/frontend source identities.25 Python/54 JavaScript local
models and syntax/disabled preview checks pass before its four reviewed
activation flags change. Actual staging completes protected input sealing and
confined module imports; the final read-only collector fails on a missing
`json` import. Original result `5671adb5…` stays false/unknown. Separate
read-only qualification `a59970c1…` verifies every sealed input/closed axe set,
the exact protected import proof, actual original import container/transport
termination, current49, control and quiet baseline; no stage/import is replayed.
One original installed native61 source8 core cohort is now running against
closure `8a36274c…` and input manifest `ac4400d1…`. It retains all three engines,
13 cases/14 network buckets,20 load samples at the unchanged2s p95 target and
100 genuine SPA cycles per engine. Other heavy work is held through the entire
cohort. No source8 browser pass is inferred before its complete result and
original browser/API/Caddy normal closure.

The first source8 cohort now closes false after1373.163s, with actual normal
browser/API/Caddy closure, `cleanup_unknown=false`, zero POSTs and5314 unchanged
archive/configuration files. Original report `91b76696…` contains Chromium's
13 passed cases,100 actual same-Document cycles,20 samples at1.876168606s p95,
30 full axe scans, one popup-IDREF proof and four named-group checks. Its global
request metadata capture refuses three valid100-selector enrichment queries:
the private collector's32-pair bound contradicts the supported101-pair request.
All14 native origin buckets contain1652 trusted GET observations;1649 detailed
request rows omit sequences204–206, and the three genuine200 responses retain
unknown sequence associations. No missing query is reconstructed. Firefox and
WebKit do not start. The raw report/root result stay false; scoped qualification
`b67e9697…` preserves those limits while retaining the completed Chromium facts.

Manual review `a508fd95…` classifies the29 serious color-contrast incomplete
scans as283 occurrences of exactly eight redundant/decorative nontext glyph
forms, all with adjacent visible text. It joins the actual raw node/check data,
pinned source, an inspected native screenshot and
[W3C non-text contrast guidance](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html). It does
not waive other incomplete findings or establish text/focus contrast or general
conformance. The separately observed popup IDREF proof remains explicit;
moderate region/heading findings stay recorded. Other engines and later editable
states still need their own actual checks. Fresh root read-only closure confirms
the original actors/container gone and current49/base5 unchanged; heavy checks
resume. A new corrected Firefox/WebKit whole-case/100-cycle target is being
prepared, with the completed Chromium scopes retained independently. All three
engines remain required before task completion.

The corrected Firefox/WebKit target is now running after its actual protected
stage/import/read-back passes (`7af15e42…`, manifest `db817855…`). Frozen
18-source closure `acff756b…` follows33 Python/71 Node/11 qualifier models and
the four reviewed activation flags. It supports the API's bounded100 selectors
plus controls, preserves actual encoded query bytes and the first refusal cause,
and retains all13 cases/14 buckets/20 samples at2s p95/100 cycles for each of the
two remaining engines. Actual Chromium qualification `b67e9697…` is an explicit
separate prerequisite; the old report and three missing query records are not
promoted or reconstructed. Original observer handles survive stage, cohort and
artifact-fetch timeouts. Heavy parallel work is held for the entire target;
neither engine nor the combined three-engine matrix is claimed complete early.


The corrected Firefox/WebKit target now passes after2917.808s, with the original
runner reaped0, raw report `673e4705…`, root result `2f4762a8…` and
`cleanup_unknown=false`. Each engine passes all13 cases and100 actual
same-document cycles,20 samples at1.953895448/1.836390193s p95,30 full axe scans,
one popup-IDREF proof and four public DOM group/name checks. No POST, budget or
request-capture failure occurs. Native AX protocol measurement remains explicitly
unsupported for these two engines. Fresh read-only closure (`7e664aac…`) confirms
the actual original API/Caddy identities and cgroups gone, original attach PID
absent, exact browser container exited0/PID0,5314 unchanged archive/configuration
files and the original base5/current49/Enforcing/no-NFS guards. The quiet lane is
released separately (`fcb7e6da…`); local parallel validation resumes. Actual
Chromium remains independently scoped by `b67e9697…`, with its original false
report and three missing query records unchanged. Manual incomplete review,
combined source8 read/load evidence, remaining installed transitions/transport,
positive native/rootless workflows and reader/zoom are still required.

Root aggregate `bfddc00b…` now independently joins the completed three-engine
read-only13-case/20-sample/100-cycle scopes, original closures and exact installed
initial JavaScript requests. Each engine requests only the main chunk:204,237
normalized gzip9 bytes against358,400; the Markdown chunk is absent. This is the
normalized installed-asset budget, separately from on-wire compression. The
aggregate preserves Chromium's original false report and three unknown query
records; complete Firefox/WebKit capture records1692/1722 trusted GETs. Actual
manual review `fcdc56bf…` classifies their exact283 nontext glyph occurrences
per engine and unique popup IDREFs against unchanged source; moderate findings
and unsupported native AX/heap protocols remain explicit. This closes only the
recorded read/load/navigation slice. All remaining installed transition,
pressure/negative, positive native/rootless and real reader/zoom work is pending.

The original installed transport-v3 attempt closes false/known before its first
controlled read: the browser collector requires UID/GID0 for a root-published
completion file, but the rootless keep-id container sees that owner as65534.
Original root result `cac5b514…` and browser report `67b6fb82…` remain unchanged;
the report records zero POST attempts. Fresh finite read-only audit `91d1ea66…`
confirms all original service/supervisor/attach identities gone, empty cgroups,
the original container exited1/PID0 and5314 unchanged archive/configuration files.
Its separate networkless probe exits0 with normal original closure. Root observes
the live probe namespace mapping and joins its namespace ID to the inner view:
host0 is unmapped, overflow UID/GID is65534, and both the original completion and
sealed typed-owner bundle retain identical inode/bytes/SHA/mode/timestamps across
the two views. Image ancestors remain native UID0 while the sealed bind root is
mapped65534. No ownership predicate is waived. A new disabled collector graph
will require that exact namespace admission and root-side publication joins;
the failed attempt is neither replayed nor promoted. Current49/base5/no-NFS and
Enforcing remain intact. No controlled transport case is accepted from this run.

Transport-v4 seals its new inputs but refuses before import because33 manifest
members exceed the unchanged private32-member loader guard. Original stage
`cb0097f9…` remains false/known with no role started. New transport-v5 omits only
the build-only script from guest upload, retaining its unchanged host source,
compiled IIFE/build proof and23 canonical module identities. Actual stage/import
`61cfc690…`/`b1d05db5…` pass, manifest `023ef7c2…` has exactly32 members, every
original transport reaps0 and its import container exits0/PID0. Its subsequent
cohort closes false/known (`7c18e9bb…`) before application startup or fixture
seeding: the import receipt includes the new namespace-helper module, while the
coordinator compares the older module map. A new version will join that exact
independently pinned row; no application transport case is accepted from v5.

Separately, headful-v8's confined import passes, but its first actual inert
Chromium visibility prerequisite stops before any application request: focusing
the second blank page does not hide the first. Browser/descendants/private Xvfb
and helpers close normally, zero requests/POSTs/phases occur, and the container
exits1/PID0. The host's combined SSH streams interleave its large JSON and stderr;
its false/unknown record is preserved. Exact read-only retrieval `2982c4fc…`
captures the protected original false/known result independently. Pinned SDK
inspection identifies default focus overrides; a new inert probe is being
prepared with precise native-behavior normalization. Actual trusted visibility
events in all three engines, repeated in each eventual Doctor context, remain
required. No application race is accepted from the inert probe.

The corrected transport-v6 import map passes its actual stage/import, then the
installed cohort closes false/known in74.346s. Original root `0414240b…` and
report `1f0b461b…` retain zero browser POSTs, six completed control commands and
normal original browser/API/Caddy closure. Its first controlled case reaches the
fresh repository return and finds a serious contrast violation on **Select
current publication** while hovered. The generic light hover background outranks
the primary action's dark fill while its text remains white. This is an
application presentation defect, not a collector refusal. Source8 acceptance is
retained for its own immutable artifacts; a new source9 snapshot will include the
hover correction, the ADR145 clarification and human guidance. A matching gate,
new native/rootless artifacts and actual browser acceptance remain required.
INV021 and ADR145 were reviewed: this preserves the existing contrast and
authority contracts and adds no invariant, API, format or dependency. Existing
installed hover-state scanning is the meaningful regression; no CSS-value mirror
unit test is added. All prior failures and unknown observations remain intact.

Source9 now freezes1528 inputs at`776470cc…`, differing from source8 only in
the primary hover CSS, ADR145 and browser/keyboard guidance. Its two matching
stock builds close normally in82.208/85.539s: native63 stock `fa1c2e8b…`, UI
`f172aad2…`, image `4d53e17a…`; rootless64 stock `ff0edfa4…`, UI `7f1cfaa3…`,
image `461059f7…`. Both existing image-foundation checks pass. The compiled
frontend digest is`1925edd5…`, distinct from the canonical source digest.
Builds use fresh owned directories on `/home`, preserve earlier artifacts and
explicitly use umask022; their original process records and complete private
logs are retained. Gate7 is running on unchanged source9. Runtime no-Node,
installation, final browser workflows and all remaining acceptance still need
their own actual evidence. Source8 results are not relabelled as source9 passes.

## Completion evidence

Completed 2026-10-29 — **WEB-020, this commit**
(`WEB-020: harden browser recovery, accessibility and bounded reads`). All six
owned rows AUTH-10, CATALOG-09 and UX-01–04 are completed with actual unit,
integration and functional mappings in the [evidence ledger](../support/web-ui/acceptance-evidence.json).

The final `scripts/check.sh --require-web --require-cockpit` original Root89443
exits0 on canonical source
`3f97731ee10f9050bef0388886b4d67d1334c5b1713f150b2c78dc33517a8034` (1528 files):
9039 backend tests pass/52 opt-in deselected in1067.78s **backend** duration;
3702 web unit/4029 combined frontend tests,95% line/90.02% branch coverage,
Cockpit, wheel installs/build, browser smoke and the final real HTTP/API React
fixture all pass. There are no skipped required checks. Final originals:

- `/var/tmp/web-020-validation-nvj5zeg7/direct-application-status-fix-gate3.stdout`:
  124539B/SHA256 `359596b0a9b74be17c7fc3e25684e051c5d090c09ebbf3844f2dcf22bf54ec8d`.
- Adjacent `direct-application-status-fix-gate3.stderr`:
  9402B/SHA256 `4dcb9afe2b7e88aa3ead1026c626002041b138997d18613fcd98b814edcffd4a`.

Direct real-Caddy/Basic application evidence includes all3 native66 catalog writes
and original result/recovery, old63→66 interface-update/privacy clearing, genuine
original-key retention across an actual API authority restart, rootless67
populated reads/configuration validation/guarded denials,1440/390 reduced motion/
fonts and native200% keyboard/zoom surfaces. Genuine Orca seven-surface control/
table/README/integer-alert/dialog/recovery speech/PCM is combined with the passing
Native68 full rejected-handle error announcement (`adf35cb3…`/6060B),0POSTs/errors
and separate normal outer closure. This is not human auditory assessment or full
accessibility/contrast conformance. Native68 build/stage/switch/HTTP passes;
canonical build610de3ca/UI-build274933cb/manifestac39b9d1/wire320c remains distinct
from final source3f97731e: only ADR145's forbidden task label/link was removed
after that build, with identical runtime/UI code. Native68 complete JavaScript
is253846 gzip bytes (entry204530/lazy49316), below358400; no fresh p95 is claimed.

Original Source9 p95/load/100-SPA/DOM/poll/encoded-retention evidence retains its
original source/artifact identities: all3 p95 values1.877/1.952/1.863s meet2s and
initial requested JS205036 gzip bytes meets358400. RSS observations, unsupported
Firefox/WebKit heap protocols and logical retention limits remain explicit;
these are recorded local-fixture measurements, not universal performance claims.
The bounded exact-fresh-byte parsing cache and virtualization preserve fresh
authority/publication joins, finite reads and no mutation retry.

The actual archive-health defect is fixed only for the four documented optional
publication category directories, with real model/dataset publication regressions
and existing sentinel/unknown/symlink refusals. The actual rejected-handle reader
bug uses an error alert for local failure and polite status for successful save,
retaining focus, original handles and no-submit behavior. ADR157/AD12/ADR113,
ADR145, INV-018/021 and affected storage/read/presentation contracts were reviewed
and aligned. Human browser/keyboard/large-library and operations guidance is
updated. No new runtime dependency, durable format, permission or execution
boundary is introduced by these corrections.

All original failed gates, collectors and unknown waits remain in the retained
history below. Unknown-exit reader observations are not typed known-exit
executions. The interrupted configuration Apply with lost original key remains
uncertain and unreplayed; catalog warning results do not claim complete technical
or integrity coverage. Rootless local mount-metadata simulation is labelled and
readonly writer-health is not called initialized. No production/NAS deployment,
merge/push/tag or Cockpit retirement occurred.

[Progress](../../progress.md#web-ui-replacement-2026-10-20) and the
[current selector](../current.md) hand off to pending WEB-021 immutable release
packaging only. WEB-021 has not started; the active multi-task plan remains active.

### Retained completion-era checkpoint history

The following checkpoints preserve their original partial/pending and failed
claims; the completed evidence above supersedes their execution status.

Source9 matching gate7 now passes0 in1507.445s with unchanged1528 inputs:
9030 backend tests (52 opt-in deselections),3702 frontend unit/4029 combined
frontend tests,95% line/90.01% branch coverage and required Cockpit, wheel, build,
startup and real API fixture checks. The separate matching HTTP fixture join
`aaf8b4de…` verifies root/prefix8 cases and100 cycles each, maximum2 active/1
waiting reads and25,178,112 reserved encoded bytes below33,554,432, six completed
service-header observations/two interruptions and final ownership drains. This
is source-built integration evidence; installed Caddy/Basic acceptance stays open.

The new asset scoped completion (`efc8bb46…`) passes with all seven new original
commands reaped, qualifying only the original native no-Node commands001–004
plus a fresh read-only inspection, one first rootless64 probe and both pinned-Node
JavaScript gzip inventories. Native63/rootless64 contain no Node or package
managers; complete inventories are254,330/254,332 bytes with204,927-byte entry
files. The original native aggregate remains false/unknown because its later
host PATH lookup failed before a PID existed; it is never rewritten or replayed.
Matching installed initial-request closures remain required.

The original new63 runtime stage remains false/unknown after offline installation,
119 wheel-file/seven-asset verification and root-tree verification, before prefix
readability, runtime TLS or INSTALLATION publication. Its final `owner.evidence`
refuses the first three commands' saved log metadata after the intervening
`restorecon -RF` changed their ctimes. Fresh read-only audit verifies5339
descendants, all four original commands reaped0 with exact intent/provenance and
closed PID/start pairs, exact original log bytes/SHA/inodes/mode/owner/mtime,
and only those six ctime differences. The fourth command's logs remain exact.
The root-private0700 prefix, empty0600 UV lock, current49 and quiet baseline
remain intact; no role or selector changes occurred. A separately reviewed
completion must join these actual facts without reinstalling or relabeling.

The new inert-only driver10/stage3 also passes protected sealing and network-none
imports (`613664ba…` input manifest, `b2cb2bd0…` import proof). It corrects only
the zero-request inert network qualifier, preserving the ordinary application's
positive-request check and all three engines'15s active/25s total native visibility
budgets. Original Chromium native hidden/visible scope remains preserved;
actual complete three-engine visibility and eventual Doctor-context repetition
are still required. No installed Source9 browser or positive workflow pass
is inferred from these preparation and integration results.

Source9 separate runtime completion-v1 now passes (`6f939d17…`) in2.495s with
all three original transports reaped0 and `cleanup_unknown=false`. It freshly
joins the exact false original stage and read-only audit, all four retained
installation commands,119 wheel leaves/seven UI assets and the5339-descendant
root-private tree before publishing readability. The new UID1000 version probe
passes; its separately owned command brings the descendant count to5345 and
the two protected receipts to5347. Only the six already audited log ctime
differences are qualified; no UV/restorecon/whole installer is replayed. The
original stage remains false/unknown. INSTALLATION and `COMPLETION-v1.json`
(`93da78be…`) distinguish that history from the completed scope. A mistakenly
nested read-only observer-log directory was separately moved to a fresh sibling
evidence location, retaining all ten original files/full9/bytes/context and
restoring the strict sealed input inventory (`45d01188…`).

The new public-helper stage-v2 passes2.152s with five original transports reaped0
(`713ff92c…`, manifest `682da1c9…`). Protected same-FD INSTALLATION and completion
file/body joins precede fresh root-inode publication. Current49, historical
control and five-process quiet baseline remain preserved; no application role
starts. The Source9 core and transport collectors are being bound to these actual
records; source-only drafts do not close installed acceptance.

The corrected inert native-visibility invocation3 closes false/known in19.562s
(`edf6b206…`, raw report `656fb12e…`). Chromium passes606.728ms with actual trusted
hidden/visible events and both original Documents retained. Firefox157 produces
no hidden event within the unchanged active budget, then closes normally;
WebKit is unattempted. All original browsers, descendants, display helpers and
container close normally with zero application GETs/POSTs. A new inert-only
same-binary Firefox test uses the existing pinned SDK's BiDi path and clears
only its two test activation/render overrides; genuine native visibility,
trusted events and same-Document proof remain mandatory. No actual new native
pass or eventual Doctor-context acceptance is inferred before execution.

Source9 core-v1 protected stage/import passes (`cfe89864…` / `a07fcd5f…`) before
any application starts. A preexecution comparison then shows the preserved
three-engine evidence would require18,047,421 pretty-printed bytes, exceeding
the unchanged16MiB private report cap. The new core-v2 changes only final JSON
whitespace: the same complete parsed records serialize to9,581,368 bytes and
roundtrip deeply equal, with originals unchanged. All request, DOM, memory,
p95, observation and combined32MiB artifact bounds remain unchanged. Four new
Python wrappers retain exact algorithms after closed namespace/flag normalization;
old sealed inputs and imports stay preserved. No browser attempt is replayed.

Core-v2 protected stage/import also passes (`0983e516…`, manifest `989c1f2c…`,
import `eb2449ca…`) with five original transports reaped0 and no unknown cleanup.
The fresh original cohort starts2026-10-28 09:27UTC under a whole-target quiet
reservation, using Source9 native63, all three engines,13 cases/14 network buckets
each,20 load samples at the unchanged2s p95 target and100 genuine same-Document
route/refresh cycles. The original host observer is374797/start5100571 on the
recorded host boot; case `055ff0ea…` uses its separately owned synthetic archive.
Its first passive observation sees11 Chromium samples/10 enriched observations,
zero POSTs and no budget failure; Firefox/WebKit have not started. These are
partial observations, not final acceptance or original-role closure. All heavy
agent testing/builds remain held through the entire target.

The separate inert native-visibility invocation5 remains false/known
(`278644e9…`, raw report `940c89e8…`) with normal original browser/display closure
and zero application requests. Chromium passes558.393ms; Firefox157 launches
through the same pinned SDK/BiDi path with the two explicit test overrides false
and creates both native pages, but does not establish initial visible state
within the existing active budget. WebKit remains unattempted. A bounded
read-only diagnostic proposal preserves this uncertainty; no cause or pass is
inferred from missing window-manager evidence.

Passive core-v2 observation8 (2026-10-28 10:13UTC) sees the same original cohort:
Chromium completes13 cases/100SPA cycles and30 accessibility scans; Firefox
completes12 cases and30 scans, with the final cycle chunk still in progress.
Both engines complete20 enriched load samples at1.876823180/1.951653755s p95,
below the unchanged2s limit. WebKit has not started. Zero POST attempts and no
budget failures are recorded. The whole-target quiet reservation remains held;
these partial records do not establish final acceptance or normal role closure.

Source-only preparation now includes positive4, rootless64, prefixed races and
zoom/reader drafts against the actual Source9 artifacts. Canonical producer
packet-v2 (`a845aa3d…`) changes only its contract inventory to the matching v4
bridge filenames; runtime sources and receipt schemas remain identical. The
zoom/reader snapshot (`2e6d60b7…`) adds durable intent and original BOOT/PID/start
records before launch input or waits, and preserves unknown guest observer
outcomes even when an SSH transport reaps. All effect flags remain false and
future installed facts remain null. Cheap source/AST and peer reviews run during
the quiet reservation; runtime models, syntax/import preflights and actual
acceptance remain deferred until its explicit release.

The original Source9 core-v2 observer now reaps0 after4337.619s. Guest result
`2ebdd5c7…` and10,205,909-byte report `84e1903c…` pass all three engines:
13 cases,20 enriched load samples,100 genuine same-Document navigation cycles
and30 full accessibility scans each, with zero POSTs or budget failures. p95
is1.876823180/1.951653755/1.863329434s against2s. Independent local qualification
`1ba92e6f…` verifies all1652/1691/1722 native GET/query/lifetime records and14
network buckets per engine. Each actual initial JavaScript request set joins
the native63 manifest at205,036 explicit gzip9 bytes below358,400. All33 RSS
snapshots are complete; unsupported Firefox/WebKit heap protocols remain so.
This establishes no heap/RSS ceiling or universal performance claim.

Fresh independent closure `e366128c…` joins the original browser CID/image/tag,
exited/PID0 state and CLI/wait, all API/Caddy/observer pairs and cgroups, then
rechecks5314 unchanged archive/configuration files and the current49/base5
guard. Its original observer reaps0. Quiet release `341963b2…` is separate from
the immutable held reservation. Completed read/load/SPA scopes `7e314f6b…`
and binding facts `fc21d020…` support the next collectors; they explicitly
leave other WEB-020 scopes false. The local verifier also passes16 refusal
models. Each engine retains31 moderate violation-rule occurrences and one
critical/29 serious incomplete-rule occurrences:852 current node-check
references require separate manual review. Zero serious/critical violations
does not close those incompletes. The actual Chromium large-manifest screenshot
`e04bd2bb…` is supplemental evidence for that state only.

The bounded native diagnostic's stage6 seals its inputs but the original
confined importer times out after10s waiting for Podman CREATE. Stage and import
remain false/unknown; no browser/display/API starts. Fresh passive evidence and
owned inspection `f688a140…` observe the exact original creator pair gone,
stable stdout and CID file naming the same container, and created/nonrunning/
PID0 state with exact image, label, user, readonly/network-none configuration
and complete original CreateCommand match. Creator exit status remains null.
Any continuation must attach once to that already-created original container,
preserve the failed records and distinguish new import closure from historical
creator uncertainty; no CREATE, installer or whole importer is replayed.

The scoped continuation now passes (`b2559bbf…`, protected import proof
`d2df4d94…`): exactly one attach starts that same original created CID for the
module import, then joins normal exit0/PID0, original wait and24 owned commands.
It publishes the first approved proof without replacing any predecessor. The
old creator's exit remains null and the old failed stage/import remain unknown;
the new cleanup result qualifies only the new attach and closure. The separate
inert invocation7 (`1112ea25…`) then closes false/known in21.113s with all original
browser/display/helper processes closed and no application requests. Chromium
proves native hidden/visible transitions in506.600ms. Firefox's three bounded
Document snapshots report visible/focused original Documents even though the
injected wait path times out; no cause is inferred. It still proves no required
hidden/visible transition, and WebKit is unattempted. A new proposal uses the
pinned SDK's original BiDi session to create a native tab in the same window
and reads actual Firefox Document visibility under the existing deadlines;
no preference, visibility emulation or acceptance target changes.

Independent manual accessibility qualification (`7854c8be…`) joins all852
current node-check references to the actual Source9 report and structural
qualification. It resolves768 redundant graphic checks through their exact
visible-label contexts and three popup ID-reference checks through unique
same-Document listbox/label/active-option joins. The81 caret checks remain
unproved: their actual axe data contains only `nonBmp`, with no numeric contrast
evidence. A supplemental actual-style capture is being prepared for seven
controls, two widths and three engines before the existing transport cases.
Numeric contrast is not inferred from source CSS or the earlier artifact.
The93 moderate rule occurrences remain explicit; this subset establishes no
universal accessibility conformance or completed WEB-020 acceptance.

The new native-tab stage7 and confined import pass (`32ca158a…` /
`9abb2a29…`), retaining the exact pinned engine/framework and already-used
read-only observer. Actual inert invocation8 (`f6e3844e…`) closes false/known
in19.842s. Chromium passes553.068ms. Firefox records its original Document
visible and registers the new page, but the native create command does not
complete within the existing observation window; the later context-ID joins
remain null. The auxiliary/browser/display/descendant processes close normally,
with zero application requests. WebKit is unattempted. The precise creation
failure is under review; no native visibility pass is inferred.

Source9 transport-v3 now passes protected staging and actual confined import
(`fd2c4521…` manifest, `76b8457e…` original proof). All five host transports and
24 original import/guard commands reap0, with unknown cleanup false. The
corrected wrappers own all fixed quiescence queries and include their final
observations in the published process inventory. The unchanged32-member cap,
15 phases/45 commands, nine UI cases, three separate typed-owner cases and
application budgets remain enforced. Its original cohort starts2026-10-28
11:57UTC against installed native63 while current49 stays selected. The bounded
caret-style prelude captures seven controls at two widths in all three engines
before the transport phases. Offline qualification has81 focused passing models
but no actual numeric-contrast acceptance yet; actual cohort/result/normal
closure are pending. Separately, the negative-response cohort is now bound to
the actual completed core and quiet-release records; its16 boundary models and
independent32-member source review pass without an installed acceptance claim.


The original transport-v3 cohort now closes false/known in187.817s
(`f630039a…` root result, `ece8e51e…` report). Chromium passes the three installed
UI cases: genuine cancellation,30.573s client timeout with explicit recovery,
and7,281,018 unchanged original response bytes with no Content-Length and a
bounded eight-row manifest window. The separate frozen-source typed-owner case
fails its requirement that both held native requests report finished; actual
records retain two failed native terminal events. Firefox/WebKit are unattempted.
The Chromium caret supplement completes14 instances/56 states; this does not
establish three-engine contrast acceptance. All41 owned commands and original
browser/descendant/API/Caddy processes close normally, cleanup unknown false.
The expected final ASGI phase/task artifact is absent, so transport acceptance
also remains open on that evidence. Both failures are under exact source/result
review; no request or used collector is replayed or rewritten.

The independent negative-response stage/import now pass (`7096bea2…` manifest,
`a4e3d938…` original proof), with five host transports and24 original import/guard
commands closed normally. Its original six-case/three-engine cohort starts
2026-10-28 12:05UTC after the prior cohort's known normal closure. Genuine scan10
503 and valid large-CJK200/client refusal acceptance remain pending the actual
result. All declared budgets and the current49 selector remain unchanged.


The negative-v2 original cohort closes false/known in86.994s (`21d80575…` root,
`acd74477…` scan10 report). Chromium records two genuine503 catalog responses
and displays the failure alert with `Diagnostic code: HFAPI005.`. Its collector
incorrectly requires exact equality with the base alert text without that
suffix, so the locator times out. The actual application message is correct;
Firefox/WebKit and the CJK profile are unattempted. Original process/dependency
closure is qualified and cleanup unknown false. A fresh collector generation
will correct the exact locator while preserving all actions, budgets and failed
original evidence. No negative acceptance is inferred from this partial result.

A later inert-stage8 prepare refuses reuse of an inherited stage7 observation
directory before creating an owner, launching a command child or creating its
new input base. The failed stage remains false/unknown (`93a5b4fe…`). Fresh
separate closure (`f42b35ac…`) verifies the intended v8 input/control paths are
absent, all fixed quiet observations reap normally, and current49/base5 remain
unchanged. The next source generation uses a new consistent control namespace;
no failed stage, browser or request is replayed.


Negative-v3 staging/import pass (`308ca5d4…` / `0a0cd00c…`). The original cohort
closes false/known in93.186s (`d884d9d6…`), with complete normal original-role
closure. Its scan10 report (`f55aadd6…`) passes all three browsers: genuine503,
exact HFAPI005/request-ID joins, correct UI diagnostic and available explicit
Refresh, zero POSTs. The CJK report (`57f69d79…`) records an actual200 manifest
response but its separate typed-client assertion fails before retaining the
result discriminant; Firefox/WebKit are unattempted for that profile. Source
review identifies a harness defect: the direct `readManifest` call omitted
`responseByteLimit`, inheriting the64MiB artifact limit instead of the explicit
8MiB limit supplied by the application session. A new meaningful private-client
build will supply the actual session constant and retain bounded result details
before assertion. The old cohort is not retrospectively accepted.

Partial Chromium caret qualification (`afd463f2…`) measures52 of56 actual states
at contrast ratios of at least10.140:1, above the unchanged3:1 requirement. Four
Facet selection group states remain unproved: the128-Tab collector sequence did
not reach focus at either width, so keyboard-open was not attempted. An actual
native click/Escape and Shift-Tab/Tab anchor is being added to the unused
transport-v4 collector within that same Tab/time budget. There is no three-engine
contrast acceptance yet and no inferred product keyboard defect.

Fresh inert stage9/import9 pass (`01ebc7e8…` / `8fef7e16…`) under the corrected
unique observation namespace. Actual invocation10 (`70d57982…`) closes
false/known in20.351s. Chromium passes551.612ms. Firefox now acknowledges native
context creation in147.206ms with exact returned/registered context-ID joins,
and its initial actual Document-visibility poll passes. Auxiliary activation
then times out before any hidden observation. Both original Documents remain
visible in the retained preactivation snapshots; the read-only X11 evidence
still observes two mapped Firefox windows. The browser/display/descendant
processes close normally with zero application requests, and WebKit remains
unattempted. No cause or native transition pass is inferred.


The corrected transport-v4 stage/import pass (`5408fba9…` / `a80e717b…`). Its
original cohort closes false/known in276.341s (`e6b1382a…` root / `b3da4601…`
report). Chromium passes all four cases, including the real queue,64 waiting
aborts, ordered original bodies and100 typed cycles. Firefox's first held-body
case records a native GET but no native Response event within the unchanged5s
header observation; the actual application reports200 with1,230 generated bytes
and zero forwarded body bytes. Server headers are not accepted as browser
receipt. WebKit is unattempted. The real ASGI shutdown artifact now exists:
normal original lifespan return/shutdown.complete, zero remaining tasks and
cleanup unknown false; its overall15-phase result correctly stays false for the
partial cohort. All42 owned commands and original dependent roles close normally.

A new private fault schedule is approved before implementation (`8729c613…`):
forward at most one byte from the genuine positive body, while holding every
remaining original byte and EOF until release. This explicitly changes the test
schedule to an incomplete-body stall; it does not retrospectively accept the
old header-only test or identify a Firefox/Caddy cause. Actual native200 and
exact request-ID observation remain mandatory before cancellation/release,
within the same5s deadline. Status/headers/body bytes, final full-body hashes,
lease/task ownership,15 phases/45 commands, queues, retention, client/phase/
cohort limits and32-member cap remain unchanged. Cancelled replies remain
incomplete and never gain whole-body identity. No preference or signal override,
synthetic positive response or product change is authorized by this correction.

Negative-v4 uses the meaningfully rebuilt separate typed client with the actual
8MiB session caller limit (`37399a08…` bundle / `41c54342…` build), retaining the
global artifact limit and30s timeout. Stage/import pass (`a621f22d…` /
`9b12530a…`). The original cohort then reaps0 in139.992s: root `4d7781c7…`,
scan10 report `f3124a92…`, CJK report `615142a2…`. All six cases across all three
engines pass with zero POSTs or budget failures. Each browser joins genuine503/
HFAPI005 and the visible diagnostic, and separately joins an actual200 manifest
response to the canonical client `bounds` refusal without rendering full
manifest facts or falling back. The independent complete server-body oracle
measures9,138,693 bytes with no Content-Length; browser-consumed bytes/hashes
remain unmeasured. All314 owned commands, four service-role invocations and two
browser containers close normally with cleanup unknown false. Scoped acceptance
`8fc8e1de…` records these six negative cases only; other WEB-020 scopes stay open.

Further partial caret review (`135c45e9…`) finds all56 Chromium and56 Firefox
states measured at a minimum10.140:1 after the native Facet anchor. WebKit and
whole-report/source-admission qualification remain pending. Exact review of the
93 moderate occurrences (`caa11045…`) retains90 unlandmarked session strips and
three h2-to-h4 file-metadata heading jumps as observed unresolved best-practice
issues. They are not waived or erased, and there is no full conformance claim.
Required actual reader/zoom smoke and the remaining serious incomplete review
are still acceptance requirements.

Native stage10/import10 now pass (`fd28ead1…` / `b5c69e43…`), with the new
read-only window diagnostic bound to the exact driver16/helper3 sources.
Original invocation11 (`3d18932f…`) closes false/known in20.539s: Chromium's
trusted hidden/visible prerequisite passes538.085ms; Firefox acknowledges its
original native-tab creation in149.644ms, then its original auxiliary activation
remains pending at the unchanged5s observation limit. All four native getter
queries complete and join the exact main and auxiliary contexts to the same
client window at both fences; the other mapped window is the default-context
startup window. These getters do not reveal selected-tab or document visibility.
The retained DOM snapshots precede auxiliary activation, and the final event
list was never collected after that failure; an empty initialized list is not
proof that no event occurred. WebKit is unattempted. All24 original commands,
browser/display descendants and the container close normally; no application
GET, POST, Basic credential or fixture phase is exercised, and current49/base5
remain unchanged.

Separate read-only inspections of the exact preserved Firefox image source
(`6ed9009a…` / `71a0eab9…`) identify an unconditional Juggler actor-registration
and top-level initialization path that sets `docShell.overrideHasFocus=true`
and `docShell.forceActiveState=true`. The later Juggler-pipe flag check only
gates its transport startup in the inspected source. This supplies a concrete
automation-override explanation to investigate; actual runtime override values
and a supported normalization path remain unproved. No engine bytes, browser
preferences, privilege settings or visibility observations were changed by
these source inspections. Native/race acceptance remains open.

The new disabled transport-v5/seam-v6 packet (`de662a9a…`) passes24 focused
models, including genuine `create_app` ASGI2.3 catalog/manifest, held lease,
disconnect, complete original-body hashes and concurrent reply coverage. Its
first incorrect422-versus400 model expectation remains preserved separately.
Finite syntax/import/default-refusal checks pass with32 staged members,
15 phases/45 commands and the unchanged typed-client bundle. Root and independent
source review (`e1f7bd33…`) find no blocking issue. Root enables only the seven
review flags (`54ac0c16…`); no product source or runtime limit changes.
Actual stage/import pass (`800292bc…` manifest / `ce4f7ace…` import), with all
five host phases and24 original import commands reaped0, no application roles
started and cleanup unknown false. The fresh original three-browser cohort
starts2026-10-28 13:23UTC. Native browser delivery, complete phase/body joins,
caret evidence and final normal closure remain pending its actual result.

That original transport-v5 cohort now reaps0 in595.741s: root `aeff4ff9…`,
report `cfad4ae1…`, outer `ae519118…`. All12 one-attempt cases across all three
engines pass: nine installed-UI cases and three separately identified
frozen-source typed-owner cases, with zero POSTs or budget failures. All15 phases
and45 Root control commands rejoin. Of18 selected ASGI replies, nine complete
with matching original whole-body bytes/hashes; nine genuinely cancelled
replies forward one original prefix byte and remain incomplete without a
whole-body identity claim. Each engine measures two active owners,64 waiters,
64 queued aborts, bounded retention below32MiB and100 typed cycles with final
zero counters. These counters describe the separate typed harness, not hidden
installed-session pools or a heap ceiling. All41 original commands, API/Caddy
waiters, browser descendants and the container close normally. Actual ASGI
shutdown completes and the app returns with zero owned tasks;5,314 archive/
configuration files remain unchanged. Pure local structural/closure review
`25f47936…` passes. Caret/manual qualification and independent acceptance review
are separate; no full WEB-020 acceptance is claimed.

The new read-only postactivation native diagnostic is reviewed and staged
(`6ac77d16…` activation / `eb784b32…` manifest / `6e4e6ad7…` import). Original
invocation12 (`2ba42350…`) closes false/known in21.185s. Chromium passes the
trusted hidden/visible prerequisite; Firefox again times out its original
auxiliary activation. This time both original retained Documents are observed
after the timeout: both remain visible/focused, and the existing main-document
trusted listener contains zero visibility events. Both read promises fulfill
within48.473ms, within the unchanged500ms diagnostic limit. Original browser/
display/descendant closure is normal and no app request, credential or phase is
exercised. The observations strengthen the forced-activity investigation without
measuring internal override values or proving an all-engine transition. The
original engine/archive and all failed evidence remain preserved.

Transport acceptance is now independently reviewed (`1191de83…`) and recorded
in the scoped completion `bcb52779…`. Core, negative and transport scopes are
complete; prefixed visibility/authority races remain the fourth read scope.

The bound offline caret qualifier preserves all19 original pure functions and
admits the exact new three-engine source/activation/import/normal-closure chain
through distinct byte-identical private input copies. Seventeen new provenance/
refusal models and independent source review (`23149f08…`) pass. After Root's
single top-level review-flag transition (`9e69f3e2…`), its original numeric
execution writes truthful incomplete output `9a3c97fd…` and exits1:42 instances,
168 states,77 of81 original caret references qualified. Four WebKit Operations
Job references at1440/390 remain unproved because their eight state captures
have fractional foreground alpha, which the unchanged conservative numeric
routine refuses. This is not a measured low-contrast result. The captured
compositing/background evidence is being reviewed before any new numeric
support or browser/product change; the used verifier and incomplete output are
preserved. Combined with the earlier771 resolutions,848 of852 current checks
are now resolved. The93 moderate findings and required zoom/reader smoke remain
explicitly open.

Root records a bounded source-implementation interpretation for the Firefox
test-fixture investigation (`3ab9b6ce…`): author a disabled transformation tool
that could omit only two unconditional Juggler focus/activity statements in a
distinct browser-data copy. The original image, executable, version, SDK and
archive must remain preserved, and every resulting run would identify a
modified test fixture with fresh affected Firefox qualification. No application
dependency, preference or privilege change is authorized. Read-only inspection
qualifies the original archive's ordinary stored-ZIP layout (`5159c0c6…`):2,582
unique entries,45,754,333 decoded bytes and no signature-member names. Separate
original-command provenance proves the exact archive pathname (`0b8c4606…`).
Actual derivation and browser use remain unapproved pending concrete tool/input/
artifact review; no overlay has been produced or mounted by this checkpoint.

The new foreground-only alpha proposal (`9b6524a5…`) confirms that all eight
WebKit Job captures contain black glyph paint at alpha0.8 over an observed
opaque RGB192 backdrop. Complete ancestor chains show group opacity1, normal
blending and no unmeasured effects. W3C source-over composition gives RGB38.4
before the unchanged WCAG luminance calculation; an independent70-digit oracle
gives8.2750077…:1, above the unchanged3:1 threshold. The new v3 qualifier changes
only that foreground domain after every existing background/effect guard; it
retains fractional-background and group-opacity refusals. Its95 unique models
and independent source review (`c63cdfc1…`) pass, preserving the earlier v2
incomplete result. Root's one-flag activation (`a6a3e522…`) then runs the new
offline qualification once: output `36065845…` passes42 instances/168 states
and all81 original caret references. Combined with the prior771 resolutions,
all852 current incomplete-review references are resolved. This does not waive
the93 moderate findings or replace required actual screen-reader/zoom smoke.

The browser-data recipe now has a closed stored-ZIP transformer, strict SELinux
context handling and independently reviewed producer wiring. Actual runtime
metadata exposes five legitimate hard-linked Python cache files; the corrected
producer requires their exact pinned link counts while keeping code, authority
and archive captures single-link. Root's derivation-only review `c2aa4e95…`
authorizes one new data copy without browser execution. That original host
attempt stops before its SSH process constructor returns: the restricted host
PATH omits the existing `rtk` executable. Its false/unknown record is preserved;
independent audit `01f356aa…` confirms no stdin delivery was reached. A separate
fresh read-only qualification (`2b425c76…`) finds the intended guest control and
overlay paths absent, the original whole archive/hash/metadata unchanged, and
current49/base5 unchanged. A fresh producer generation will pin the actual host
executable and its explicit PATH. No modified archive or browser pass is inferred
from the failed attempt or its separate absence qualification.

The new v4 launcher packet (`b6bf91ad…`) passes12 focused checks and independent
review (`97b47e8c…`). Root's separate whole-SSH-locator assertion precedes its
single fresh execution; the actual owned intent then rejoins that exact vector.
The derivation passes0 with normal original closure (`98358ec2…`), producing
the distinct46,218,395-byte overlay `cefddbe7…`. All2,582 member joins preserve
the original archive and all other decoded member hashes; only the two intended
statements are omitted. Actual protected Root-result and derivation receipts
are retained for full readback before browser-foundation admission. Browser
execution, native transitions and application acceptance remain unproved.

Full protected receipt readback now passes (`5ee2e469…`), and Root independently
rejoins all2,582 member names/offsets and the sole decoded-member change
(`302dda5d…`). A separate inert-only admission is sealed (`77a63dec…`).
The new bound native19 generation passes source review and seven focused new
binding checks; stage13 and confined import pass normally with24 owned commands.
Its one actual invocation14 remains false/known (`cc54adfd…`): Chromium and
the explicitly modified Firefox fixture produce trusted hidden/visible events
in533.838ms and918.412ms. WebKit reaches initial-visible but fails the unchanged
five-second native step; its exact failed action/wait and live event-listener
state are unmeasured. The report's empty event array is initialized data copied
only after a successful sequence. All three browsers, their displays/descendants
and the container close normally;25 owned commands are reaped, with only the
browser attach returning1. Current49/base5 remain unchanged and no application
request or POST occurs. The failed original and used sources are preserved;
WebKit source diagnosis precedes any fresh diagnostic. No all-engine native,
race, fresh Firefox performance or application acceptance is inferred.

The subsequent read-only artifact survey passes (`f22b6858…`) with26 owned
commands closed normally. Both51/63 raw installation receipts,119 package
leaves and six assets each, UID1000 installed version/wire probes and the
existing browser/runtime identities rejoin. The new63 raw installation digest
is measured directly; no parsed-JSON reserialization supplies that identity.
No browser, application role or HF archive is touched by the survey.

Native20 adds only bounded diagnostic markers and actual retained-document/
listener reads. Its one invocation15 remains false/known (`18ed5eaa…`), with
normal original closure: Chromium and the modified Firefox fixture pass.
WebKit's auxiliary activation actually fulfills; the main hidden-state wait
reaches its fixed deadline and its original promise rejects with TimeoutError.
Three complete same-document snapshots show both documents still visible,
main focus changing to false, and the actual main listener retaining zero
events. This resolves the prior diagnostic uncertainty without qualifying
WebKit visibility. Native tab selection and exact input targeting remain
source-only follow-on work; no new native input or acceptance waiver follows.

The bounded native-keyboard revision now passes focused checks and independent
refusal-path review (`ca22bbf7…`). Stage16 and confined import pass with all24
owned commands reaped. Its single invocation17 (`9ca092dd…`) closes false/known:
Chromium and the explicitly modified Firefox fixture pass in540.125ms and
935.298ms. WebKit's current-namespace, private-display and native input ownership
checks pass; its CtrlT helper sends four acknowledged key events, releases its
owned keys and exits0. The original automation auxiliary-Page promise remains
unfulfilled until the existing five-second detail deadline. No focus-traversal
Tab step runs. Native GTK tab creation and automation adoption are unmeasured;
the successful input helper does not establish either. Independent closure
`2b15b1e2…` rejoins the exact SSH vector, all25 guest commands, normal browser/
display/descendant/container closure, unchanged current49/base5 and zero app
requests/POSTs. The failed original remains preserved. All-three native proof,
the fourth read scope and remaining WEB-020 acceptance stay open.

Native23 adds a source-backed fixed AltHome blank load, guarded by the original
main Document/URL, an actual trusted hidden event, one raw proxy in the original
context and the same owned native window. Thirty new JS/Python delta models,
15 wrapper checks and final independent review (`502b1855…`) pass; stage17 and
confined import close normally. Its one invocation18 (`a227922e…`) remains
false/known, while measuring further progress: WebKit creates and publishes the
same-context blank page, five native Tab steps establish actual auxiliary
focus, and preparatory PgUp returns to the unchanged visible/focused main.
Counted PgDn then completes its input helper without selecting the auxiliary:
all three retained-document pairs show the main still visible/focused and the
auxiliary hidden; the actual listener retains its two preparation events and
zero new events after the counted baseline. The original hidden wait times out.
All nine helper operations exit0 with26 acknowledged key events, released owned
keys and known input state. All three browsers/displays/descendants close
normally, current49/base5 stay unchanged and no application request or POST
occurs. Chromium and the modified Firefox prerequisite pass in575.764ms and
902.333ms. The original failed result and used sources remain preserved; no
all-three native, race or application acceptance is inferred.

GTK4.14.5 defines previous-page selection cyclically, so native24 changes only
four direction literals to use the already measured PgUp action for both
selections. Six new direction checks, five wrapper projection checks and
independent review (`9ee61f18…`) pass; helper bytes, guards and deadlines are
unchanged. Stage18/import pass normally. Its one invocation19 (`46f3af0f…`)
also closes false/known: tab materialization, five-step focus and preparatory
return pass, but counted PgUp from the main page leaves that retained document
visible/focused and the auxiliary hidden in all three actual diagnostic pairs.
The listener still has two preparation events and zero new counted events;
the original hidden wait times out. All nine input helpers close normally with
26 acknowledged events and known released input. Independent local qualification
`40505490…` joins normal original browser/display/container closure, unchanged
current49/base5 and zero app requests/POSTs. This rules out direction alone as
the remedy. The next source-only work investigates bounded native dispatch logs;
no additional shortcut, dwell, retry or deadline increase follows from this
failure. All-three native and the remaining acceptance stay open.

Native25 adds only bounded GTK dispatch logging and exact mapped-library
capability checks, preserving native24's input sequence, helper, guards and
deadlines. Sixteen new JS logger/capability models,15 new Python terminal-file/
transport models and independent source review (`3f48a3df…`) pass; stage19 and
confined import close normally. Its single invocation20 (`bffa55b0…`) remains
false/known. Chromium and the modified Firefox prerequisite pass in538.574ms
and939.132ms. WebKit's tab materialization, auxiliary focus and preparatory main
return pass, but counted selection leaves the actual main visible/focused and
the auxiliary hidden; the unchanged hidden-state wait fails. The39,426-byte raw
post-attachment log (`d49352d4…`) has joined Node/Root file identity, byte counts,
hash, EOF and normal process closure without overflow. Actual mapped GTK
capability passes. Preparatory PgUp reaches the Notebook change-page action;
counted PgUp logs a GtkTextView move-cursor action without that later dispatch.
WebKit uses an internal GtkTextView for key translation, so these logs alone do
not identify the focused widget or prove WebProcess consumption. Exact source
interpretation is active before any further input change. Independent local
qualification (`0bc1ebe0…`) rejoins the raw capture and stream/terminal receipts,
all25 owned commands, normal browser/display/container closure and all nine
normally closed input helpers with26 acknowledged events and known released
keys. Current49/base5 remain unchanged and no app request/POST or Basic read
occurs. This does not supply a fresh archive-file survey or change the failed
native result. Failed results and all used source generations are preserved.

Independent review of the disabled Python5/JS6 race graph (`151a5ae3…`) found
two ownership gaps: stopping a still-live container without qualifying native
input closure, and treating missing CID assignment as absence after CREATE was
already invoked. A new disabled generation is correcting these paths with
conservative preservation and explicit CREATE-attempt tracking. It retains the
existing authentication handoff, inputs, budgets and original long observer.
No full-race admission or execution is inferred from source preparation; the
all-three native prerequisite and every remaining task acceptance stay open.

Native26 uses GTK's existing CtrlAltPgUp previous-page binding for only the two
counted selections, retaining preparatory CtrlPgUp. Reducing the Tab allowance
from8 to6 preserves36 keys, five chords and all deadlines. Exact combined-only
XKB map checks precede READY/input, with2/4/6 operation arity propagated through
JS/Python. Nine new Python helper models, nine JS models,15 wrapper models and
four Python-to-Node contract checks pass; independent source review (`a63003bf…`)
passes. The first VM fixture failures are preserved and corrected without
weakening runtime assertions. Stage20/import pass in11.289s with all five host
phases and24 confined-import originals normally closed.

Its single invocation21 remains false/unknown. The outer original SSH is reaped1
and its result `881bb2d7…` preserves the complete52,580-byte guest JSON
`baeccad9…`. Current-container namespace proof and the same-inode runtime handoff
pass, then the original attach observer expires at the unchanged300-second
collector deadline (304.802s overall). The attach has no proved closure; the
terminal report/log/container-state and final baseline branches were not reached.
No per-browser transition result is inferred from earlier invocations. Retain
the exact CID, process pairs, public runtime, browser state and original journals.
A fresh bounded read-only inspection is being prepared; it has no cleanup,
signal, input or replay authority. The native prerequisite, race scope and all
remaining task acceptance stay open.

The separate read-only observer (`852569cc…`, independently qualified by
`7593552f…`) closes its own SSH normally and locates the stalled path. The
retained report records Chromium/modified Firefox passed; WebKit's helper8
refuses the combined-key map guard before READY, without a frame-delivery
intent. It reports successful Prior lookup with raw mask0, fails the old
expected12 assertion and terminates in0.037s. Exact helper namespace identity
is absent while init/Node/attach remain live. The combined shortcut was never
exercised; the observed preparatory input is distinct. Empty-owned-input flags
do not establish a fresh global keyboard-state sample or original stream EOF.

Published libX11 source and release manuals identify the returned mask as
consumed, whereas the archived manual used for native26 called it unconsumed.
The new disabled native27 revision records the raw mask and independently
derives remaining modifiers. Its narrow pre-READY refusal path must join the
same original child/logs, zero frame/events and normal failed exit within the
original budget, preserve the first failure and forbid later input before
clearing only the cleanup dependency latch. Current installed library/source
identity remains a separate required join. It neither modifies nor repairs the
retained native26 Node; further fixed-path read-only evidence is being prepared.
No cleanup signal, replay, native pass or race admission follows from this
source work, and all used results remain unchanged.
