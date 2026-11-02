# WEB-030: Reuse compatible Library facets during pagination

| Field | Value |
| --- | --- |
| Status | pending |
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

Authorized; awaits dependency. Depends on WEB-029 so request measurements use the reviewed compact
Library. Production latency and installed-profile behavior remain unmeasured by
the planning investigation; this package makes no rollout claim.

## Completion evidence

Pending implementation authorization, activation, request-count and correctness
results, invariant/ADR review, gate evidence and the completed progress entry.
