# WEB-029: Bring Library search and results into view

| Field | Value |
| --- | --- |
| Status | pending |
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

Authorized; awaits dependency. Depends on WEB-028 as the plan's chosen priority order. Implement
with owned synthetic metadata; no production archive or service access is needed.
Request-pipeline changes belong to WEB-030.

## Completion evidence

Pending implementation authorization, activation, viewport/accessibility results,
contract review, gate evidence and the completed progress entry.
