# WEB-030: Reuse compatible Library facets during pagination

| Field | Value |
| --- | --- |
| Status | completed |
| Plan | [Protect unsaved configuration and streamline Library browsing](../2026-11-02-plan-web-drafts-and-library.md) |
| Depends on | [WEB-029](web-029-compact-library-browsing.md) |
| Authorization | User authorized implementation and activation on 2026-11-02 |

## Scope and acceptance

Avoid rereading unchanged browser facet evidence on ordinary Next/Previous
actions while retaining fresh catalog and row-enrichment reads.

1. Read the requested main catalog page freshly before deciding reuse. Reuse a
   facet only when it is successfully decoded and its normalized filter intent,
   authenticated authority/generation, archive/configuration context, catalog
   identity and entire scoped coverage match the new main read. Apply the
   existing facet-compatibility checks; an operational fingerprint alone cannot
   establish unchanged tags or publication membership.
2. Ordinary Next/Previous with unchanged compatible evidence uses at most four
   GETs: the main page and existing inventory, status and revisions enrichment.
   Preserve fresh joins by type/ID and exact SHA/publication/generation. Missing
   or incompatible facets obtain fresh bounded reads and cannot invent counts.
3. Initial load, changed filters or page size, explicit **Refresh library**,
   authentication changes and changed catalog evidence obtain fresh facets.
   Explicit refresh remains a request for fresh evidence even when identities
   ultimately match. Tag-only changes must invalidate incompatible facets even
   when the operational configuration fingerprint is unchanged.
4. Retain each finite loaded facet page and its continuation meaning, including
   manually loaded tag pages; never present a loaded subset as all facet values.
   Changed scope/identity retires incompatible continuations before reuse.
5. Preserve the existing bounded pipeline rather than introduce a background
   loader. Keep the current two-reader Library batching and all shared read,
   encoded-retention, response, page, retry and time ceilings. Reuse must not
   create uncharged aggregate copies or a second unbounded cache.
6. Preserve stale-cursor restart, cursor-cycle/page-limit refusal, independent
   partial/failure evidence, route departure, session changes and late-response
   fencing. A fresh main read and reused facets do not establish a global
   snapshot or authoritative current-publication enrichment.

Primary files are `web/src/library/library-state.ts` and related Library
state/component tests. Any shared QueryStore change must be justified by this
task and retain its other owners' semantics. Independent asynchronous facets,
inactive-route memory reclamation and backend query caching are deferred.

## Contracts, invariants, and ADRs

Review INV-018 and INV-021 in the [register](../../../invariants.md),
[ADR145 Library composition](../../../adr/decision-145.md#typed-library-composition-amendment-2026-10-26)
and [catalog queries/coverage/pages](../../../discovery.md#queries-coverage-and-pages).
Amend the affected browser composition requirements to describe compatible
browser reuse and explicit refresh semantics. Update the
[Library paging guide](../../../web-ui/library.md#page-and-bookmark-a-bounded-read)
where needed. This is browser evidence reuse after a fresh authoritative main
read, not permission to bypass the server's fresh metadata-read requirements.

## Validation

- Add state/component regressions with exact endpoint/method counts for first
  load, Next, Previous, explicit Refresh, changed filters/page size, missing
  facets and identity/coverage mismatches. Assert at most four GETs on the
  ordinary compatible path, versus the recorded eight-read baseline.
- Cover tag-only curation changes, same-SHA replacement publications, changed
  fingerprints, individually failed facets and partial facet pagination.
  Reused counts must match their qualified scope, never table-page length.
- Delay facet responses in an owned fixture and verify compatible paging avoids
  those requests without increasing concurrency; report deterministic request
  reduction separately from any measured end-to-end timing. Do not claim a
  production latency improvement from artificial delay.
- Exercise late replies after filter/session changes, stale/cycling cursors,
  route departure and Back/Forward. Preserve no-hidden-follow-up-read and exact
  join regressions. Confirm browsing submits no POST or Hub request.
- Run a built-browser pagination/Refresh workflow against owned API fixtures,
  record source and request evidence, update contracts/guidance and run
  `rtk scripts/check.sh` before the `WEB-030` commit. Close the parent plan only
  after all three tasks and plan-wide acceptance have actual evidence.

## Execution notes and handoff

Activated after WEB-029 commit `afde038`. Depends on WEB-029 so request measurements use the reviewed compact
Library. Production latency and installed-profile behavior remain unmeasured by
the planning investigation; this package makes no rollout claim.

## Completion evidence

Activated after WEB-029 commit `afde038`. Reviewed INV-018/021, ADR145 Library
composition and discovery query/coverage semantics. Contract-first amendments in
those records and the paging guide define fresh-main compatibility and explicit
Refresh. Reuse stays in existing charged QueryStore facet slots with small
provenance metadata; no server cache, endpoint, wire/durable format, dependency,
authority or runtime-bound change. Browser baseline uses the compact WEB-029 built source, manifestd9b0d842… /
source9af61679…, with the same fixed25-row incomplete-coverage fixture and an
artificial75ms delay on each facet response. `browser-S6JyfW` passes10/10.
Measured API GETs initial/Next/Previous/explicitRefresh are8/8/8/8, each with4
facet reads, noPOST/Hub/CSP/external and peak2 active API handlers. Fixture-only
walltimes are1245.631/691.524/559.915/618.349ms respectively; these artificial-delay
measurements are separate from deterministic request reduction and establish no
production latency. All comparisons retain actual source/manifest and per-stage
method/path evidence. Final source validation is recorded below.

Existing successful WEB-029 throwaway fixtures alone retired after complete
compressed per-entry file hashes/symlink/special metadata, unchanged second
inventory and exact-root/device/mount/no-live-owner checks. The retained record
`.scratch/web029-gate2-success-temporary-retirement/` binds179,580 entries and
595,958,300 regular bytes; compressed manifest SHA256
`d7058126d82305c2a66d2a10cd55e9994efe52d13a054e20cb76de40d542e6c0`.
All original raw gate/browser results and both failed-gate archives remain.
Implementation validation follows.

Implementation is frozen: only Library state and its unit tests change product
behavior; QueryStore, joins, controller/coordinator and all runtime budgets are
untouched. Facet slots retain bounded filter/auth/API-owner metadata beside their
existing charged handles, without aggregate body copies. The same compatibility
predicate gates reuse, visible facet qualification and drift/restart handling.
Only Next/Previous opt in; successful fresh main decoding precedes the decision.
Incompatible continuations retire before replacement; compatible manual pages
and cursor-cycle history survive.

Focused191/191 and query/retention22/22 tests pass, with scoped/global types,
ESLint/Prettier and whitespace checks. Exact commands from `web/`:
`rtk node node_modules/vitest/vitest.mjs run test/library-state.unit.test.ts test/library.component.test.tsx test/library-joins.unit.test.ts test/library-filters.unit.test.ts test/App.component.test.tsx --reporter=json --outputFile=.artifacts/web030-focused-final.json`;
query/retention uses the same runner with `test/query-state.unit.test.ts`,
`test/query-state.component.test.tsx`, `test/retention-budget.unit.test.ts` and
output `.artifacts/web030-query-retention.json`. Expanded state57/57 report is
`web/.artifacts/web030-state-3.json`. Coverage includes per-facet missing/failure,
all scoped-coverage fields, normalized filters/page size, wrapper archive/fp,
tag-only curation with unchanged operational fp, same-SHA new publication/gen,
manual tag pages/cycle/Refresh, main-delay ordering and late reusable Next after
filter/session/departure/disposal plus fresh reconnect. Existing exact joins,
stale restart,32-page/cycle and no-hidden-follow-up tests remain. Independent
source review finds no material issue. Initial lint's dynamic-delete style was
corrected before freeze; no focused test failure is claimed as acceptance.

Final built-source Chromium `web/.artifacts/browser-XHoNvy/report.json` passes
11/11 in57.9s, SHA256
`3870760bcb3c838a1f5603e4c47d1396db6cf4eb0eb294efc5ee84de3885268d`.
Before report SHA256
`7004f4aa8ea45341e4a7ba92bbb5971b0e0ba24bf40b604c576ce14f74eeca1e`.
Both use the same default fixture and75ms artificial facet delay. Actual stages:

| Action | Before API GETs/facets | After API GETs/facets | Before → after fixture ms |
| --- | --- | --- | --- |
| Initial |8/4|8/4|1245.631 →799.860|
| Next |8/4|4/0|691.524 →253.432|
| Previous |8/4|4/0|559.915 →252.502|
| Explicit Refresh |8/4|8/4|618.349 →564.952|

Paging and Refresh issue zero other GETs; ordinary4API GETs are4total GETs.
Peak API handlers stays2, and every action starts with the fresh main catalog.
All three enrichment requests retain the exact displayed25 selectors and row
publication evidence. Changed catalog identity Next performs the existing
one-restart-to-first-page9GET path; compatible Next then4. Same-ID whole-coverage
change8; text/page size/Clear/Back/Forward each8 with fresh facets. All traffic
GET, no Hub/external/CSP/page errors. Deterministic request reduction is the
performance result; artificial-delay walltimes establish no production latency.

Actual200% zoom rerun passes in
`web/.artifacts/library-zoom-ss2tmJ/result.json`, SHA256
`74bd0d79a9e7108a09a627e2cdd94683f8607f153671efcee540a312a801a278`.
Sandbox PID2407522 closes and is absent; browser zoom2,320×500CSS, no overflow,
full axe/CSP/errors/external clear. Final matching manifest
`31b466730cf5bf900d7e586e2297ea96d7ada7333f6941a171ae41c8edee38e3`,
source `ea5f67fc26fe554ad1cb65647d4e9de520e896595cd776718fb1fbde6f940d49`.
Existing WEB-028 draft/navigation and WEB-029 viewport/keyboard/warning workflows
pass in the11-case run. Earlier screenshots retain their original WEB-029
provenance; none are relabelled or overwritten. This is owned source-fixture
Chromium evidence, not installed native/rootless or production acceptance.

Strict `rtk scripts/check.sh --require-web --with-build` passes exit0 in
1602.803s under the reviewed private read-only archive shadow as login UID1000/nice10.
All1,249 inputs/names remain unchanged; full raw log SHA256
`5ccb1c4e58dc9029eaa45a33dac24d17c202c0f69cf7dd30b34f5d897e40f602`. All9,594backend,
4,115combined frontend (3,757unit subset),19functional metadata,16wheel tests,
three locked installation profiles, exports/strict fixtures/lint/types/build,
11built Chromium workflows, actual200%zoom and real HTTP/API React fixture pass.
No required frontend skips;95.17% lines/90.15% branches. Gate browser
`web/.artifacts/browser-y2wXAW` and zoom
`web/.artifacts/library-zoom-20FAh5` preserve the accepted final source/manifest,
with exact owned browser closure. There was no failed full-gate attempt for this
package; earlier package failures remain separately preserved.

The independent final audit rechecks current-build viewports at scrollY0:
390×844 search209.4375–251.09375 / identity820.921875–838.921875;
1440×1000 search182.71875–224.375 / identity636.125–654.125.25rows and no page-wide
overflow both. Initial navigation is12total GETs:8Library API plus4shell assets/
bootstrap; the table above counts Library API reads. Next/Previous4GETs are total
network GETs, with no shell reads. The remaining changed-evidence/intent workflow
records73API GETs over its10stages, all with exact expected facets and scope.
All plan-wide source/browser acceptance is verified. Final successful generated
fixtures alone retired after complete compressed metadata/file hashes and a
second unchanged inventory, with exact inode/device/mount/no-live-owner fences.
Record `.scratch/web030-gate1-success-temporary-retirement/` binds179,583 entries
and596,030,468 regular bytes; compressed manifest SHA256
`7d9b7df4c50b7d0db91e998f2573aa11833b90edfe05d202dc887d7ad0c659fd`.
All gate/browser results, both earlier failed-gate archives and unrelated files,
including root `node_modules/`, remain retained.

INV018/021, ADR145 and discovery/paging guide amendments are current; independent
source and evidence review has no findings or remaining scoped criteria. This
commit completes WEB-030 and the approved plan, updates progress and clears the
active selector. No deployment, live services/archive, runtime dependency,
draft persistence, operation replay, release/tag or push. Actual installed-profile
acceptance and production latency remain outside this source/fixture scope.
