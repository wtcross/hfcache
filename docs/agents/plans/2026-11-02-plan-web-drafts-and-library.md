# Protect unsaved configuration and streamline Library browsing

| Field | Value |
| --- | --- |
| Status | completed |
| Created | 2026-11-02 |
| Authorization | User instruction on 2026-11-02 authorizes implementation and plan activation, sequential WEB-028 → WEB-029 → WEB-030 |
| Tracker | [Current plan](current.md); completed and selector cleared |
| Starting source | `main` at `5e2261f`; reconcile Git and task records before activation |

## Outcome and scope

Protect configuration edits during an explicit installed-configuration reload,
bring Library search and repository rows into the first screen, and reduce
repeated facet requests during ordinary pagination. Use three source work
packages so draft safety, presentation and query changes remain independently
reviewable. Task files own status and completion evidence.

The investigation found three useful baselines; these are findings, not
implementation acceptance:

- A focused component reproduction showed that one reload click followed by a
  failed configuration GET removed a dirty draft without a confirmation. The
  existing guide explicitly describes discard-on-reload, so the new behavior
  requires a deliberate contract amendment.
- An isolated source Chromium fixture at 390 by 844 CSS pixels placed Library
  search about 958 pixels down and the table about 2,207 pixels down. At 1440
  by 1000, the table began about 1,089 pixels down. These are synthetic local
  layout measurements, not production or installed-browser performance claims.
- A normal nonempty Library page uses the catalog read, three enrichment reads
  and four facet reads. Next/Previous currently repeat that pipeline. Request
  amplification is established by code; production latency was not benchmarked.

The scope stays within existing configuration and Library workflows. File-path
search, configuration-list filtering, operation-history presentation, a separate
mobile-menu change, inactive-route memory reclamation and independent background
facet loading are deferred. No backend cache, endpoint, durable preference,
runtime dependency, archive format or authority change is proposed. Implementation
and ordinary source validation do not authorize deployment, live archive work,
service changes, release/tag/push, or changes to the completed migration's holds.

## Contracts and decisions

Review these records before each affected implementation package, and amend
living contracts before changing behavior in the same commit:

| Area | Authority and intended treatment |
| --- | --- |
| Draft and exact-base editing | [INV-001 and configuration security](../../invariants.md#configuration-and-security), [configuration guide](../../web-ui/configuration-and-tags.md#compare-concurrent-changes-without-losing-intent), [ADR153](../../adr/decision-153.md#structured-editor-composition-clarification-2026-10-26). Clarify successful replacement after an explicit dirty-draft decision; keep one bounded RAM-only draft and exact original base. |
| Browser evidence and recovery | [INV-021](../../invariants.md#replacement-browser-ui-design), [ADR145](../../adr/decision-145.md), [ADR154](../../adr/decision-154.md#browser-application-and-recovery-composition-clarification-2026-10-26). Preserve private-state invalidation, original operation handles, preview binding and uncertain-effect blocks. |
| Library meaning and identity | [INV-018](../../invariants.md#tags-and-supplemental-discovery-metadata), [catalog queries](../../discovery.md#queries-coverage-and-pages), [typed Library composition](../../adr/decision-145.md#typed-library-composition-amendment-2026-10-26). Retain provenance, whole scoped coverage, finite pages, exact joins and catalog-identity checks when reusing browser facet evidence. |
| Presentation and access | [Library guide](../../web-ui/library.md), [browser and keyboard guide](../../web-ui/browser-and-keyboard.md). Describe disclosures, active filters, focus behavior and refreshed evidence accurately. |
| Execution | [Planning](../planning.md), [workflow](../workflow.md), [agent invariants](../invariants.md), [conventions](../conventions.md). Activation, evidence and one gated commit per package follow the existing loop. |

No new architectural decision is expected within these boundaries. Implementation
must record the invariant/ADR review and amend affected records; introduce a new
decision only if the actual design adds or changes an architectural rule.

## Ordered task records

| Order | Work package and task file | Depends on |
| --- | --- | --- |
| 1 | [WEB-028: Preserve unsaved configuration during reload](tasks/web-028-preserve-drafts-on-reload.md) | None |
| 2 | [WEB-029: Bring Library search and results into view](tasks/web-029-compact-library-browsing.md) | WEB-028 |
| 3 | [WEB-030: Reuse compatible Library facets during pagination](tasks/web-030-library-pagination-reads.md) | WEB-029 |

Execute sequentially. The order prioritizes data-loss prevention, then the
largest visible browsing improvement, then request reduction. Each package
includes its own tests, human-guide updates, contract review and gate; a separate
validation-only implementation package is unnecessary.

## Acceptance and validation

1. A dirty manual reload requires an accessible explicit decision. Cancelling
   makes no request. During replacement, admitted edits remain visible; a
   same-authority failed read preserves the exact raw form, prepared intent
   and original base. Successful replacement resets all three together,
   including when the base revision is unchanged. Session invalidation still
   clears private evidence and fences late replies.
2. With the default collapsed advanced filters and a fixed loaded fixture,
   search and the first repository identity appear without page scrolling at
   390 by 844 and 1440 by 1000 CSS pixels. Preserve a visible incomplete-coverage
   qualification. At 320 pixels and 200% browser zoom, controls and evidence
   remain usable with labelled horizontal scrolling confined to wide tables.
3. Expanding or collapsing filters makes no request, preserves entered text and
   leaves the applied query unchanged. A compact summary distinguishes active
   filters from unsubmitted form edits. Bookmarks, Back/Forward, model/dataset
   predicates, tag provenance, selections and all evidence scopes retain their
   current meaning.
4. Ordinary Next/Previous on unchanged normalized filters and matching catalog
   identity/coverage uses at most four GETs: one catalog and the existing three
   enrichment reads. Initial loads, changed filters/page size, explicit Refresh
   and incompatible catalog evidence obtain fresh facets. No concurrency,
   retention, byte, page, retry or time bound increases.
5. Draft replacement and browsing introduce no automatic POST, operation replay,
   silent merge, false health/empty result, or borrowed publication authority.
6. Run focused state/component regressions and built-browser keyboard/layout
   workflows against owned fixtures. Record source, fixture, viewport, actual
   request counts and browser scope; retain failed evidence separately from
   later passing executions. Run `rtk scripts/check.sh` before each implementation
   commit. Source-browser checks do not establish installed native/rootless or
   production acceptance; record any separately required operator handoff.

For plan drafting, validate local links, reciprocal task/dependency references
and whitespace only. No implementation gate result or completed work-package
progress entry is claimed by this draft.

## Lifecycle and amendments

- 2026-11-02: Draft and pending task records created from the user's planning
  request. The current selector remains inactive. No implementation is started.
- 2026-11-02: Draft validation passes for all five new/updated planning files:
  42 local links/anchors, reciprocal task links, dependency order, whitespace
  and the inactive selector. No application or implementation gate is claimed.
- 2026-11-02: Independent review adds stale reload-decision invalidation and
  accessible recovery for invalid fields inside collapsed filter groups.


- 2026-11-02: User authorizes implementation and activation. Git inspected at
  `5e2261f`; original planning files and unrelated root `node_modules/` preserved.
  Select WEB-028 first, retaining draft investigation evidence as historical.

- 2026-11-02: WEB-028 completes with64 focused regressions, five built Chromium
  checks and the full strict gate. Failed long-temp gate and verified preserved
  fixtures remain separate from the passing short-temp retry. Select WEB-029.

- 2026-11-02: WEB-029 completes with matched before/after source-fixture images,
  measured first-viewport results,87 focused/19 driver tests,9 built-browser
  workflows, actual200% zoom plus keyboard-choice supplement, and the full strict
  gate. Failed gate-harness run and complete fixture archive remain separate;
  strengthened67-case harness and full retry pass. Select WEB-030.

- 2026-11-02: WEB-030 completes in this commit after191 focused/22 retention
  tests,11 built-browser workflows, current-build viewport and actual200% zoom
  checks, deterministic4-total-GET compatible pagination and the full strict
  gate. ExplicitRefresh remains8API GETs; changed identity preserves bounded
  restart. All three task and plan acceptance criteria pass. WEB-028 `b6e8060`,
  WEB-029 `afde038` and this WEB-030 commit remain separate. Source/owned-fixture
  scope only; earlier failed evidence and unrelated root `node_modules/` are
  preserved. No deployment/live/archive/operation/dependency/release/push scope
  is activated. Complete the plan and clear the active selector.
