# WEB-015: Implement repository configuration and tag management workflows

| Field | Value |
| --- | --- |
| Status | completed |
| Plan | [Web UI replacement](../2026-10-20-plan-web-ui.md) |
| Phase | P3 |
| Depends on | [WEB-014](web-014-safe-markdown-rendering.md) |
| Branch | `feat/web-ui` |
| Work-package commit | `WEB-015: implement repository configuration and tag management` (this commit) |

## Read before implementation

Config read/validate/plans/applications; typed managed edits; detail/Library selections; original-operation controller; tag normalization.

Also read the relevant sections of [architecture](../support/web-ui/architecture.md), [API contracts](../support/web-ui/api-contracts.md), [testing strategy](../support/web-ui/testing-strategy.md), [acceptance matrix](../support/web-ui/acceptance-matrix.md), and [human documentation map](../support/web-ui/documentation-map.md). Load only affected living contracts and ADRs through their indexes. Refer to the [source review](../support/web-ui/source-review.md) for pinned baseline evidence; current git wins over it.

## Scope and implementation requirements

Build structured global/repository forms and a safe supported advanced view from the server editable projection. Add model/dataset entries, change supported settings, enable/disable/remove configuration and edit tags from detail or Administration. Display canonical tag normalization/suggestions and limits. Historical unmanaged tags are not directly editable; explain reconfiguration. No separate annotations store or tag CRUD endpoint.

Use one dirty draft, reviewed diff, exact base revision, validation and required sizing preview before Apply. Invalidate readiness on every edit and stale server revision. Preserve protected fields through server managed edits; never serialize redaction markers as real values. Removing/disabling config is not purge; changing retention is not immediate deletion. Distinguish authority changes requiring manual provision/restart from invalid syntax.

Integrate application receipt/confirmation and read-only uncertainty reconciliation. Concurrent tabs/config writers get an actionable compare/reload/re-edit conflict; do not auto-merge silently or overwrite unseen tags. Navigation warns about unsaved draft; no persistent TOML storage by default. Error codes map to fields where safe and remain visible independently of transport failures.

## Unit and component validation

React tests cover add/edit/remove forms, tag normalization/duplicates/max, hidden protected values, dirty navigation, validation invalidation, preview/apply button gates, failed Envelopes and historical-tag read-only behavior.

## Integration validation

Run the UI client against actual helper/config endpoints for ordinary/tag-only/global edits, wrong permissions, missing preview, stale base and install-unconfirmed states. Validate final exact configuration with backend models.

## Functional validation

Three-browser Caddy workflows add model/dataset with tags, preview/apply and verify detail/facet updates; concurrently edit tags in two tabs; preserve conflict and unknown apply; disable/remove a repository and prove archived bytes remain.

## Human documentation deliverables

Complete configuration-and-tags.md with step-by-step flows, conflict examples, exact success criteria, side effects and manual authority-change limits. Update troubleshooting and UI guide screenshots.

## Acceptance

Tags and configuration are genuinely manageable through the SPA with the same guarded apply pipeline, correct provenance and no lost protected data or false install success.

The task also requires the existing `scripts/check.sh` gate plus strict applicable web/Cockpit and functional checks described above. New capabilities are not completed solely by adding test descriptions. Update actual test-to-case mappings and run them. Documentation and relevant contract/invariant/ADR updates land with the behavior, not in a later catch-up task.

## Completion evidence

Completed2026-10-26, WEB-015, this commit. The SPA composes the existing guarded
read/validation/preview/application APIs: one RAM-only exact-base draft, complete
repository entries, reviewed diff, protected-field preservation and explicit
original-outcome observation. Configuration grants remain independent; host-read
is not an extra prerequisite. API receipt state never substitutes for protected
host outcome. No endpoint, runtime dependency, TOML editor or replay path is added.

INV001/018/019/020/021 and decisions133/145/153/154 were reviewed; affected living
contracts and dated ADR amendments record this composition. The actual client
bugs found during acceptance are fixed: route-specific null operational
fingerprints remain valid for configuration reads without weakening identity
joins; same-origin browser JSON POSTs preserve native Origin with the
`same-origin` referrer policy while GETs retain `no-referrer`. Server CSRF checks,
CSP, credentials, redirects and no-retry rules remain strict.

### Current source, artifacts and checks

Evidence root `E=/var/tmp/web-015-validation-a_bndq7a` below is an actual retained
host directory. Native fixture0.2.30 projects only the recorded version fields;
canonical software remains0.2.2. Rootless0.2.31 is unexecuted in this package.

| Proof | Actual result / locator |
| --- | --- |
| Frozen source |1457 inputs, `bc1d0602cbba4dbd9e3720607680f85ae0817aa34d6c0caf19e93ba678013c83`; parent`1ca6287` |
| Full strict gate | `scripts/check.sh --require-web --require-cockpit`, exit0/1645.369s, no hash/mode drift; `E/gate3/strict-gate-result.json`, SHAd8ab3c63fec427a884ee4c405826ad270d1f3e062d070c2ef35c0f0bf08b2e41 |
| Gate coverage |8597 backend/52 unrelated opt-in deselections;581 Cockpit unit/110 mounted Firefox;3496 web unit/3697 combined;95.84% line/91.04% branch. All required lint/types/wire/docs/build/wheel/startup/read-API stages pass; zero required skips. Log SHAabe54a798178e677545d3b03b1a84ba10574dfc5551c94bcf282cd251d1965ba |
| Current artifacts | `/var/tmp/web-015-artifacts-source3-a_bndq7a/stock.json`, SHA1e3319c4ec6abfb3c22fafdc32b62f69f4836d2c7caf0f94b67ec9c0a6958953; wheel535669B SHA2383881d7234150b351854b78be2c01334c3f928b36790b6142dd27f42bdec55 |
| UI / image | UI1ed82384a44231572e2e8004192df256553ffcb8998383814820d23705a4383f; image`sha256:e6193e0be8b4407590f3b4f3ff694a837ec6e01c64f14b0b89cf0103014f9d51` |
| Source / foundation / runtime | `E/artifact-source-proof-source3.json` SHAb9623cab628621e85b0d9e50448eaaa99152b3a63ea41002cb1a814509010d61 rejoins1457 frozen/1463 projected inputs and pinned UBI10micro ancestry. `E/image-no-node-proof-source3.json` SHA95ea1aaf766121d3f1c86698e24247f0b547c984064e85b493a8e0bcd5cdb863 exits0 under UID981/read-only root/network-none, no runtime Node/package managers. |

### Actual installed workflows and CONFIG-12 mapping

Normal8 passes exit0/976.213s, generation`eb89c58685d248b6881836c5aff1092d`:
33 one-attempt cases,11 each Chromium156.0.8078.4/Firefox157.0/WebKit27.2.
`E/functional-normal8-result-observed.json` SHA601546118024fed11a270e07547ffb98e4677e6d1b7379ae329eae78992ae21d;
`E/functional-normal8-browser-report-observed.json` SHAa0cadea6ea2f08348ca3c5924a7ef4540788f940fe1944cda07e4e70b09743b0.
Actual forms add model/dataset/tags, validate and size against the real owned
HTTPS Hub, apply and explicitly confirm; two-tab tag-only conflicts preserve the
losing draft/full-byte base, while disable/remove preserve archived publications.
Global settings, supported JSON, dirty navigation, historical reconfiguration,
Library choice controls and current detail/facet updates are exercised.

Twenty-four original keyed operations yield12 confirmed/no-pending applications;
543 trusted requests are507GET+36POST, including12 nonkeyed validations. Four
contiguous256-bound buckets per engine retain every request without interception
or overflow. All66 CSP checkpoints/dialogs/popups/page-errors are clear. Full9,
SID and byte snapshots preserve archive files, original lock, exact predecessor
chains and protected inputs. Ten original process pairs are gone, three cgroups
empty, five endpoints refused, fixed inputs/five baseline pairs unchanged;
`cleanup_unknown=false`. Native CA inheritance/restoration is verified; actual
Hub info/tree/HEAD sizing returns zero payload bytes and zero rejected requests.

The final original-uncertainty cohort passes exit0/84.722s, generation
`17cc6b54fc7b46c4824e5d850ee3a675`, three one-attempt Chromium cases.
`E/functional-uncertainty1-result-observed.json` SHAf6bf09e3bf864a16fb6e5a819040976997aef7fa8820cf3f3d0154b518768f43;
browser report SHAfe0accaad36704e94f0261bdc44dde2dd2e59a2b02e5ca7334dafc38157e24e3.
An explicit fixture entry delta retains the genuine confined helper/unit and
exits91 only at `exchange:after_rename`. Original application
`91d3d99acf3963769f18a2cc0f1d06dc` remains API`interrupted`, protected
`installed_unconfirmed`/`pending=true`. Reload/recovery observes its original
key/ID with GET only: no replacement Apply, host confirmation claim, rollback,
pending clearance or receipt rewrite. Configuration/candidate/backup/pending,
private history and API-store full9/bytes remain intact. Twenty-five original
process pairs are gone; cgroups/endpoints drain, inputs/baseline remain exact and
`cleanup_unknown=false`. The known pending fixture state is intentionally retained.

[CONFIG-12 evidence](../support/web-ui/acceptance-evidence.json) binds real nodes:
unit draft/state/ports/editor/choice/navigation/recovery plus null-read/origin
regressions; actual API grants/preview/queued refusal and real framed Unix
configuration-writer integration; all11 normal and3 uncertainty browser IDs.
Controlled fetch/authority/SID adapters are labelled separately from installed
native/helper evidence. Existing WEB008 rootless/core acceptance is preserved;
this package proves native UI workflows, not the later WEB022 platform matrix.

### Preserved failures and deliberate fixture preparation

Every original failed result remains false; no partial browser pass is promoted.
All locators below are under `E`. Normal2–8 retain their
`functional-normalN-result-observed.json`, browser report, `.log` and `.result.json`;
normal1 uses the explicitly listed `functional-normal1-observed.json`.

| Attempt | Actual failure / retained evidence |
| --- | --- |
| Initial baseline / native profile | Raw-TOML/default comparison refused before CONFIG/archive/service effects (`native-baseline1.log`); missing raw repositories key refused before selector/store changes (`native-profile1.log`). Original private inputs remained; checked V3 preparation staged only8 known files through the owned export backing, never by writing `/srv/hfcache`. |
| Source2 build setup | ENOSPC (`stock-build-source2-launcher.log`); wrong interpreter refused before output (`stock-build-source2b-launcher.log`). Exact explained cache cleanup retained all source/evidence/guest/tagged artifacts; separate successful outputs remain distinct. |
| Normal1,55.624s | Genuine null configuration-read fingerprint exposed the client bug; six GET/zero POST. `functional-normal1-observed.json`; original source1 gate1 PASS1533.099s remains historical. |
| Normal2,143.778s | Private second-tab CDP body reread failed despite rendered draft; original confirmed327532… application and plan retained. Source2 gate2 PASS1617.756s remains historical. |
| Normal3,265.541s | Private202 CDP body reread missed an actual successful preview; original ea94c6… plan and confirmedb57a… application retained. Observer now uses strict actual Location/key/route and independent receipt/result joins. |
| Normal4,322.452s | Combined removal/reconfiguration/mobile case exceeded its60s private deadline after four confirmed applications; split preserved all assertions. Empty final candidate and full original store/history retained. |
| Normal5,382.551s | Chromium10 passed; Firefox validation403/HFAPI010. `functional-firefoxdiag-result-observed.json` separately proves actual Origin:null/authentication present; zero keyed diagnostic operations, normal drain. |
| Normal6,182.009s | Combined two-tab setup/preview guard expired; originalccc4088570e9a03ca404b71661b02375 plan actually succeeded/complete in7.908s, result`normal6-plan-result-observed.json` SHAff437c05e8d042a07c12769d1b72b2df1fba1fdf7828f7c6a4ccbaacd357dd45. No original replay. |
| Normal7,154.633s | Combined Apply/Library/detail guard expired after confirmedc16ccd… application, without product/CSP/response error. Private whole-case guard became180s; API20/readiness55/network256/overall1800 and all assertions stayed fixed. |

Normal2–8 preparations authenticated the original confirmed candidate and positive
drain, preserved known backup/configuration bytes and whole API stores by same-FS
NOREPLACE. When already empty, preparation moved only the store. These are
explicit new fixture changes or opaque state retention, never retries of an
uncertain operation. Original application histories/inodes remain retained.
Source3 focused Firefox diagnostic now proves200/exact Origin/readiness before
intentionally stopping without a plan; its raw expected-false diagnostic result
and prior403 record remain (`functional-firefoxdiag-source3-result-observed.json`).

### Human documentation and handoff

Configuration/tag, Administration, Library/detail, Operations and troubleshooting
guides plus relevant API/client/security/configuration/server/discovery contracts
are current. Three actual Chromium screenshots were copied byte-exactly and
visually reviewed; captions identify owned synthetic inputs. Post-caption
`uv run --locked --extra server --extra mcp python scripts/check-docs.py` passes
215 human documents/27 helpers. No future job UI is claimed.

Final plan/documentation regressions pass72 tests in12.95s:
`pytest tests/unit/test_web_plan.py tests/unit/test_docs_alignment.py tests/unit/test_docs_config_contract.py -q`.
Documentation alignment again passes215/27, `git diff --check` is clean, and all1457
frozen implementation hashes/modes remain unchanged after evidence/caption edits.

After all roles drained, root normally stopped the original owned Hub process
178593/start9977245 and restored its original stopped state in0.549s
(`E/owned-hub-stop.log`/`.result.json`). Its counters, API store, configuration,
pending/candidate and original lock/key are preserved. The final known
installed-unconfirmed/pending fixture is quiescent and deliberately uncleared.

These are genuine installed native/Caddy/helper workflows over the owned read-only
loopback NFS export with strict synthetic publication inputs, not production/NAS
ingestion/verification, new rootless UI or full platform acceptance. Earlier core
rootless evidence stands; WEB022 and final compatibility/parity/acceptance remain.
No production/NAS/live Cockpit, rollout, merge, push or tag action occurred.
[Progress/handoff](../../progress.md#operator-handoff) records completion;
[WEB-016](web-016-operations-and-reports-ui.md) is next through the
[current selector](../current.md).

## Browser-control compatibility input

Prior renderer diagnostics prove that native `select` creation in the owned
WebKit27.2 engine attempts inline style under the application CSP (diagnostic
/var/tmp/web-014-validation-xowemz0k/csp-diagnostic1-evidence.json). Recovery
choice groups are corrected with radios in the preceding package. Configuration
and Library editing must use CSP-compatible choice controls and exercise actual
CSP observations; review the five existing Library selectors during this scope.
Do not relax CSP or manufacture permissions/readiness to accommodate a control.
