# WEB-029: Bring Library search and results into view

| Field | Value |
| --- | --- |
| Status | completed |
| Plan | [Protect unsaved configuration and streamline Library browsing](../2026-11-02-plan-web-drafts-and-library.md) |
| Depends on | [WEB-028](web-028-preserve-drafts-on-reload.md) |
| Authorization | User authorized implementation and activation on 2026-11-02 |

## Scope and acceptance

Reorder and condense Library presentation so primary browsing is visible before
the full filter form. Preserve all existing query and evidence meanings.

1. Put search, repository type/scope, known matches and access to results first.
   Condense scope summaries and move technical filters, detailed coverage and
   tag suggestions into labelled accessible disclosures. Keep a visible warning
   when metadata coverage is incomplete, including zero known matches. Current
   versus retained scope and tag provenance remain clearly discoverable.
2. Show a compact applied-filter summary and a clear reset action. Distinguish
   applied predicates from form text still awaiting Apply. A bookmarked technical
   filter remains visible in the summary even with its disclosure closed.
3. Opening/closing a disclosure makes no request and changes no query, fragment,
   selection or form value. Keep hidden filter controls mounted and enabled as
   appropriate so collapsing a group cannot omit its values from FormData.
   Keyboard focus must remain visible and outside a group when it is collapsed.
   If Apply finds an invalid hidden field, reveal its disclosure and focus the
   field or its associated error so the user can correct it directly.
4. Condense the Library's repeated introductory text and put session/version
   controls into a consistent compact location, retaining their labels, notices,
   disabled states and explicit invocation. Keep recovery/update-required
   guidance visible when relevant and leave other workspaces usable.
5. On a fixed loaded fixture with ordinary authenticated state, 25 rows and
   incomplete metadata coverage, the search control and first repository
   identity must appear within the initial viewport at 390 by 844 and 1440 by
   1000 CSS pixels, with advanced filters collapsed. Additional failure/update
   notices may use necessary space; they must never be suppressed to pass.
6. At 320 CSS pixels and 200% browser zoom, all controls, active predicates,
   warnings and pagination remain reachable. Page-wide horizontal overflow is
   absent; existing wide tables retain labelled keyboard-accessible scrolling.
   Preserve readable text and target sizes rather than shrinking the whole UI.
7. Filtering retains debounce, explicit tag/technical Apply, dataset model-field
   clearing announcements, provenance and publication scopes, bounded fragments,
   Back/Forward restoration and loaded-page selection/copy behavior. Layout
   changes do not add automatic catalog, host, Hub or configuration requests.

Primary files are `web/src/components/Library.tsx`, `web/src/styles.css` and the
Library-facing shell in `web/src/App.tsx`. Reuse existing primitives and CSP-safe
choices. Durable layout preferences, new sorting/filter capabilities, a general
shell redesign and separate mobile-menu behavior changes are outside this task.

## Contracts, invariants, and ADRs

Review INV-018, INV-019 and INV-021 in the [register](../../../invariants.md),
[typed Library composition](../../../adr/decision-145.md#typed-library-composition-amendment-2026-10-26)
and [catalog query semantics](../../../discovery.md#queries-coverage-and-pages).
Update the [Library](../../../web-ui/library.md) and
[browser/keyboard](../../../web-ui/browser-and-keyboard.md) guides, with actual
new screenshots identified by source/fixture scope. Do not relabel old screenshots
as current. Record whether presentation changes require an ADR clarification;
unchanged authority requires no invented architectural rule.

## Validation

- Extend Library/shell component tests for disclosure state, exact preservation
  of unsubmitted values, applied-filter summaries, bookmarks and no extra reads.
  Include hidden invalid numeric inputs, dataset switches and cleared filters.
- Capture matching before/after built-browser screenshots and DOM measurements
  at both acceptance viewports. Record search and first repository identity
  positions, fixture state and actual viewport; old investigation numbers are
  context, not the new baseline measurement.
- Exercise keyboard disclosures, choices, table scrolling, selection/pagination,
  Back/Forward, 320-pixel layout and 200% zoom. Run axe on normal, expanded and
  warning states, and check actual CSP violations. Record which browser engines
  were exercised; source tests do not establish installed-profile acceptance.
- Verify configuration dirty-navigation protection from WEB-028 remains usable
  after shell-control placement changes. Update human guidance and run
  `rtk scripts/check.sh` before the `WEB-029` commit.

## Execution notes and handoff

Activated after WEB-028 commit `b6e8060`. Depends on WEB-028 as the plan's chosen priority order. Implement
with owned synthetic metadata; no production archive or service access is needed.
Request-pipeline changes belong to WEB-030.

## Completion evidence

Activated after WEB-028 commit `b6e8060`. Contract-first updates describe compact
disclosures, visible applied-versus-unsubmitted scope, retained hidden values and
validation recovery in discovery and human guides. INV-018/019/021 and ADR145
Library composition reviewed: presentation changes no authority, query predicate,
publication join or architectural rule; no invented new ADR is required. Browser baseline preceded all production layout edits. The Library query pipeline
is unchanged; presentation does not add catalog/host/Hub/configuration reads.

Focused component regressions pass87/87, exit0, report
`web/.artifacts/web029-focused-3.json`; exact command from `web/`:
`rtk node node_modules/vitest/vitest.mjs run test/library.component.test.tsx test/App.component.test.tsx test/bootstrap.component.test.tsx test/configuration-navigation.component.test.tsx test/configuration-recovery.component.test.tsx test/OperationRecovery.component.test.tsx --reporter=json --outputFile=.artifacts/web029-focused-3.json`.
Scoped ESLint/TypeScript pass. The existing installed functional driver's
Library disclosure/summary interactions are updated while preserving exact query,
row, href and scoped-publication assertions; its19 metadata tests pass in
`web/.artifacts/functional-driver-JmrnHn`. This is driver upkeep, not installed
native/rootless acceptance.

Built source-fixture Chromium baseline `browser-tNkE7t` passes7/7. Final
`web/.artifacts/browser-LX9Goq/report.json` passes9/9 in35.2s (including WEB-028
raw-form/navigation cases), using the actual built bundle and fixed synthetic
25-row/50-known-match/50-publication fixture with25 usable/25 missing observations.
Both start at scrollY0. Measurements are CSS pixels:

| Viewport | Search before (top–bottom) | Identity before | Search after | Identity after | Table before → after |
| --- | --- | --- | --- | --- | --- |
|390×844|958.328–999.984|2313.313–2331.313|209.438–251.094|820.922–838.922|2206.563 →714.172|
|1440×1000|663.234–704.891|1195.594–1213.594|182.719–224.375|636.125–654.125|1088.844 →529.375|

Each baseline/final initial load records8 API GETs, zero POST/Hub/external requests,
zero CSP/page errors,25 loaded rows and no page-wide horizontal overflow. Final
normal/expanded and320-CSS-pixel zero-known-match warning states have zero axe
violations. Keyboard disclosures, preserved hidden raw fields, explicit Apply,
invalid-hidden-field reveal/focus, applied/unsubmitted summaries, scope/provenance
bookmarks, Back/Forward, selection/copy, paging and labelled table scrolling pass.
Four actual matching before/after PNGs are saved under
`docs/web-ui/images/library-source-fixture-*`; prior screenshots remain untouched.

Actual200% Chromium browser zoom passes in
`web/.artifacts/library-zoom-WNV2DY/result.json`: owned temporary profile/extension
calls `tabs.setZoom(2)` and independently observes `getZoom()==2`. Outer640×1000
becomes320×500 CSS pixels, DPR2, visualViewport.scale1 and CSS zoom1. Controls,
hidden validation, keyboard horizontal table scrolling, pagination, warnings,
no page overflow and full axe pass. Sandbox remains enabled; exact browser PID
2365101 closes and is absent. It is actual browser zoom, not CSS/pinch/device-scale
emulation. Both final workflows bind manifest
`d9b0d8425837c88aae146fe53cfc393693287fb7cd49c4c2062c44e2c06194c0`, source
`9af61679a8169dabe8faef82d9be486b391b5ea5a365dbfa6e3166b31a3e3343`.
This is owned built-source evidence, not installed/production acceptance.

Earlier failures remain separate: `browser-OaIPaW` records the mobile identity
28px too low and a missing banner landmark; source spacing/refresh placement and
landmark fixes resolve them without suppressing warnings. The zoom harness's
initial import/cache-ordering error and `library-zoom-oR60Wn` landmark failure
remain retained; `browser-iba74A` and `library-zoom-5A7BV0` are interim passes.

The required web gate now includes `test:library-zoom` after `test:browser`, with
owned-browser lifecycles sequential. Playwright's test-only global budget120s and
wrapper150s accommodate the added cases; product read, retry, retention,
concurrency and time bounds are unchanged. Development guidance and required
script checks reflect this added regression. Complete successful WEB-028 throwaway
fixtures alone are retired after compressed full-entry manifests, exact root/
log bindings, no-follow/device/mount/live-owner checks and second inventories;
`.scratch/web028-success-temporary-retirement/` retains the records, and all raw
logs/results/browser evidence plus the failed gate archive remain intact.

Supplemental built-browser acceptance in
`.scratch/web029-supplemental2-7q7eaypv/result.json` closes the independent audit's
keyboard-choice/nondefault-summary gap without changing frozen source. At actual
200%/320×500CSS, ArrowDown/End/Home/ArrowDown/Escape preserves focus, fragment and
8GETs; ArrowUp/End/Enter selects retained scope with8 more GETs. Explicit Bits4
Apply adds5GETs for a qualified zero-known-match query (no row-enrichment reads).
The collapsed applied summary is fully in view at x18/y375.172/w284/h40.938.
Full axe/CSP/page/external errors0, all GET, exact PID2371151 closed/absent.
Result SHA256`76a9b9fd6a2a6f7f4d33b656afdba3adf9f1e730db85734fcf18c65a67d7020c`.
Before screenshots bind manifest648ab2d9…/source1e081051… (WEB-028-built app);
all four copied PNGs independently byte-match their retained captures. The updated
functional-driver DOM selectors also pass an owned Chromium probe with exact50
matches/50publications, including mounted closed coverage; record
`.scratch/web029-driver-selector-LWWWeZ/result.json`.

First strict gate is retained as a failure: exit1,28 failed/9,562 passed, all
failures in `tests/unit/test_check_web_gate.py`. The new required zoom script and
stage were omitted from that fake-tool harness's file/stage declarations, and its
help expectation retained old wording. Product/browser behavior is unchanged.
All1,248 inputs/names stayed unchanged during this failed run; raw
`.scratch/web-drafts-library-validation/web029-gate1.log` SHA256
`5fa9242fbd1bd9946256dabcb12ce1f07a5ca365f85ce70bf4a0a27dd6d38ad3`.
The strong prerequisite/failure/order harness now covers the added stage,
including late helper disappearance. All67 focused gate-control tests pass in2.45s:
`rtk uv run --locked --extra server --extra mcp pytest -q tests/unit/test_check_web_gate.py --no-cov --junitxml=web/.artifacts/web029-gate-controls.xml`.
Ruff format/lint and whitespace pass. Existing refusal/order/no-later-stage
assertions remain intact; only fixture declarations and the expected help text
are extended. Product artifact source9af61679… is unchanged. The full strict
retry passes as recorded below. Failed fixtures
are fully preserved in `.scratch/web029-gate1-retirement/`:159,622 source entries,
159,623 members,288,217,239 regular bytes, complete contents/symlinks/FIFO/socket
metadata verified against unchanged source with no live owners or descendant
mounts. Archive SHA256
`fef06a4f60472acfbee940bc4be22c37b4412a29eda23d2d0464a4448c14daee`;
manifest SHA256
`12ce8861dcecae5c30e77357acab46dcd8d171bf9beb3e59276766c59090fefd`.
The exact owned temporary root retired after another full verification
(retirement-result.json); all failed logs/results/archive/manifest remain retained. The completed retry and closeout follow.

Strict `rtk scripts/check.sh --require-web --with-build` retry passes exit0 in
1598.967s, login UID1000/nice10 under private read-only empty archive shadow.
`web029-gate2-result.json` records all1,248 inputs/names unchanged; full raw log
SHA256`d27b36d6c7cf6563da05b2e53bb35205280658e6710d834fd1337bfba4958913`. All9,594backend,
4,077combined frontend (3,719unit subset),19functional-driver metadata and16wheel
tests pass, along with three locked installations, generated contracts, lint/types,
build,9built Chromium workflows, actual200%zoom and real HTTP/API React fixture.
No required frontend skips;95.12% lines/90.10% branches. Gate browser
`web/.artifacts/browser-cU0Iy7` and zoom
`web/.artifacts/library-zoom-YBb0v3` both pass with normal closure. Final artifact remains
manifestd9b0d842…/source9af61679…, matching independent browser acceptance.

Independent review finds no remaining source or acceptance gaps. INV018/019/021
and ADR145 review is recorded above; presentation changes no architecture or
runtime authority. Guides, four actual screenshots, strengthened gate, task,
progress and next-task selector are current in this commit. Only source/owned
fixture acceptance is claimed; installed native/rootless and production behavior
remain unmeasured for this change. No deployment, live services/archive, runtime
dependency, durable preference, draft persistence, replay, tag or push. Select
WEB-030 after this commit.
