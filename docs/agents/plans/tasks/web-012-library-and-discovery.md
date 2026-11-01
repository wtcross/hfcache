# WEB-012: Implement the unified model and dataset Library

Interface-only instructions and source references have been omitted from this
retained shared record. Exact original text remains in Git `c692d7ae4b866fefd8a743a21afdb729da0f39c4`;
original document path SHA-256 `220d4f347d869ca40ccdd85d6b00169aac551251cdd96ecf85b24f7ebdca101a`,
original content SHA-256 `ce35910722deb01eeb771a9d9ec0b6f0393c1dd7251a824b8faacba461d19844`.
Historical proof hashes identify the original artifacts, not this edited record.

| Field | Value |
| --- | --- |
| Status | completed |
| Plan | [Web UI replacement](../2026-10-20-plan-web-ui.md) |
| Phase | P3 |
| Depends on | [WEB-011](web-011-query-and-operation-state.md) |
| Branch | `feat/web-ui` |
| Work-package commit | WEB-012, this commit |

## Read before implementation

Catalog query/coverage models and routes; repository/status read shapes; approved Library screenshot; interface filter semantics.

Also read the relevant sections of [architecture](../support/web-ui/architecture.md), [API contracts](../support/web-ui/api-contracts.md), [testing strategy](../support/web-ui/testing-strategy.md), [acceptance matrix](../support/web-ui/acceptance-matrix.md), and [human documentation map](../support/web-ui/documentation-map.md). Load only affected living contracts and ADRs through their indexes. Refer to the [source review](../support/web-ui/source-review.md) for pinned baseline evidence; current git wins over it.

## Scope and implementation requirements

Build the dense accessible Library table with All/Models/Datasets, configured/archived/all and current/retained scopes, literal ID/tag search, all/any tag filters/provenance, format and model-only variant filters. Encode only supported API query keys; reflect filters in deep links and clear incompatible dataset/model predicates deliberately. Preserve normalized values while presenting readable labels and debounced finite reads.

Join catalog rows to bounded status/revision metadata by validated type/ID and authority, not array position. Keep known matches, coverage, configured/enabled/archived/unmanaged and last-observed tags distinct. Summaries must state scope and source; don't invent archive-wide disk usage or counts from a single page or double-count hardlinked logical bytes. Page/reset correctly on stale cursors and explicit budget failures, without hidden unbounded collection.

Actions use explicit reviewed canonical selected repositories and current permissions. No partial-weight selection or unbounded bulk-all-results mutation. Friendly empty and unavailable states preserve unknown coverage. Large results are virtualized/paged, keyboard usable and responsive.

## Unit and component validation

Test filter combinations, exact query grammar, all/any/provenance, model-only dataset refusal, Unicode query bounds, same-variant semantics and table empty/error/coverage states.

## Integration validation

Call real catalog/status with all fixture repository states, page/limit changes, curation-only invalidation, stale cursor, malformed responses and selection changes; verify stable keyed joins and bounded requests.

## Functional validation

Three browsers through Caddy perform ID/tag search, filter a model variant, switch to datasets/configured/unmanaged, page and return via deep link. Assert no unsupported upstream request and no false 'no matches' under incomplete coverage.

## Human documentation deliverables

Create library.md and update root navigation; explain scopes, search boundaries, unknown technical evidence, logical sizes and filter combinations with synthetic examples/screenshots.

## Acceptance

The Library exposes existing hfcache discovery and inventory accurately with bounded requests and useful filters; model/dataset/provenance distinctions and unknown coverage survive all read states.

Historical execution summary: the recorded gate included the retired interface; exact invocation and original proof remain in Git `c692d7ae4b866fefd8a743a21afdb729da0f39c4`.

## Execution notes and blockers

Completed2026-10-26 from WEB-011 `e0bedca`, one work package in this commit.
The Library composes existing typed catalog/status/inventory/revision GETs under
the shared authenticated controller. Bounded fragments preserve bookmarks while
the authenticated shell retains its query refusal. One displayed page, explicit
facet continuations, at most100 loaded selectors and32 cursor positions reuse
the32MiB retained-data budget,8MiB read ceiling and two global read slots.
No hidden full walk, mutation, Hub read, endpoint or runtime dependency was added.
Current configuration/last-observed tags, unknown coverage and exact current versus
matching retained publications remain separately attributed. Route/auth changes
fence late reads and selection; dataset selection deliberately clears model-only
predicates. Full detail/README/editing/job workflows retain their later tasks.

Gate1 exposed an immutable Location mock in an existing recovery test; only that
fixture was corrected to follow real browser history while preserving API origin.
All8 recovery tests then passed. No runtime code changed after the first freeze.
The first installed source has1421 frozen inputs at
`5b46b3926d1fb622952cc26adcf2f60fc10ed3e39a4b6e19e6b5521084ab9ce7`;
final gate2 has1421 inputs at
`421e7f8cb7fbc2cfcfd003a8ee9a4f032d10b276172951cd7db79a2aa67d8f4e`.
`artifact-gate2-source-proof.json` records the sole test-only difference and1420
other exact matches. Actual screenshot links and plan/evidence bookkeeping are
excluded from that runtime/test/contract freeze and checked again before commit.

Failed functional1–6 remain retained. They exposed private-driver CDP response-body
observation, a bootstrap response-shape mistake, select-label matching and missing
Firefox test trust. Functional4 has no browser report and remains failed, never
inferred as passing. The corrected driver uses an additional actual same-origin
GET oracle rather than intercepting/replacing application responses. Existing
Firefox certificate-install policy supplies the test CA with TLS verification and
all sandbox controls enabled. All original owned cohorts drained; no operation
was submitted or replayed. There is no unresolved WEB012 acceptance blocker.

## Completion evidence

- **Strict gate:** `rtk proxy python3 -B .scratch/web-012-run-strict-gate.py --attempt 2`
  executes `historical gate invocation (original command SHA-256 `dfe15d4ee16e8207e5ddfe1138f7416950f8e6013a5d77e8aa230bfd51dccdc4`; Git `c692d7ae4b866fefd8a743a21afdb729da0f39c4`)`: exit0,1442.837s,
  zero source drift.8581 backend tests pass (52 unrelated opt-in deselections),
  581historical frontend unit and110 mounted Firefox cases,3234web unit and3337combined
  component cases pass. Types/lint/format/contracts/strict fixtures, locked wheel
  profiles, builds, two startup Chromium cases and real HTTP/API React reads pass;
  zero required skips. Web coverage:94.55%statements,91.82%branches,
  93.72%functions,95.78%lines. Local Library checks additionally passed103 unit
  and19 component cases, including invalid filters, source drift, exact joins,
  failed/empty/partial states, history and immediate unmount/no-hidden-read cases.
- **Evidence root:** `/var/tmp/web-012-validation-aw9l6_l2/`; gate2 log SHA256
  `a7743a3b4c4dfa0c1b772e138e19c2d9926fed1a99c9d6ac822b5d2de94f4dcc`;
  gate2 result SHA256
  `9d2cb2a6e7b2723cf3a0da6a383aa3682a02a99f7fac5b0dad3fb1084cd2fb44`.
  CATALOG01–05 now map actual unit/component, real catalog/ASGI integration and
  installed functional nodes in [the acceptance ledger](../support/web-ui/acceptance-evidence.json).
- **Installed functional:** `rtk proxy python3 -B .scratch/web-008-call-guest.py --script /home/webfixture/web012-inputs/web-012-run-owned-functional.py --log /var/tmp/web-012-validation-aw9l6_l2/functional7.log`:
  exit0,475.491s,42 one-attempt cases (14 each in Chromium156.0.8078.4,
  Firefox157.0, WebKit27.2). Built UI → trusted real Caddy → installed native
  fixture0.2.20 API exercises all scoped read workflows;227 observed trusted GETs
  per engine, zero POSTs/interception/overflow. Same-variant counterexample,
  current/retained exact pairs, all/any/current-only tags, unmanaged/unpublished,
  coverage-zero qualification, main/facet pages, reload/back, invalid fragments,
  keyboard selection and narrow-screen overflow pass. Full9 archive identities
  and bytes, configuration and real query summaries stay unchanged; operation
  count0. All original roles/descendants/cgroups/endpoints drain normally, with
  five baseline infrastructure pairs unchanged. `functional7-evidence.json` SHA256
  `f302ddbf9468ac79f301a8020d97547b33a680fbe0c34e39727f402f077f8804`;
  guest cohort `36431c44687e46e49cf332da1eea61e9`.
- **Artifacts:** `/var/tmp/web-012-artifacts-aw9l6_l2/stock.json` records stock
  API/UI image `a0e509cc029a12f97f3f9067d708db3aa53b71ad58aafc47de6efa90228c144c`,
  wheel SHA256 `bf7c9dc67d988357b97068aeb318d9b8bbed89a3f9d612c6edb38f5a449a7776`
  and UI manifest SHA256
  `e3d427ad9b0f6e8d5d4266439c82eb22390c0dd25a00cad9abce9174523fd258`.
  Pinned UBI10micro ancestry, stock CA/foundation and actual absence of
  Node/nodejs/npm/pnpm/yarn/corepack pass. All114 installed Python modules match
  the wheel. Only copied project/lock fixture version fields project0.2.2 to0.2.20;
  canonical version and real release selection are unchanged.
- **Human contracts:** [Library guide](../../../web-ui/library.md), actual synthetic
  desktop/mobile screenshots, navigation, troubleshooting, discovery/API-client
  and development guidance accompany the feature. INV018/021 and ADR133/145
  were reviewed and amended for scope/provenance, finite read composition and
  exact identity; no new architectural authority or dependency was introduced.
  Final documentation alignment passes213 human documents/27 helpers. The four
  documentation/plan suites pass78 tests in14.07s; diff checks pass. All1421 frozen
  file hashes/modes and the router symlink remain exact in
  `precommit-source-preservation.json`. See the
  [progress entry and operator handoff](../../progress.md).
- **Scope:** real installed application/business reads use explicit owned local
  NFS-metadata simulation, not NAS or full native/rootless platform acceptance.
  Required later platform/parity/compatibility and final gates remain. No production,
  credentials/guards/calendars, installed predecessor interface, merge/push/tag or rollout action.
  Next: [WEB-013](web-013-publication-detail-pages.md).
