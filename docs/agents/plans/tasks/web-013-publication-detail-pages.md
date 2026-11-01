# WEB-013: Build rich exact-publication model and dataset detail pages

Interface-only instructions and source references have been omitted from this
retained shared record. Exact original text remains in Git `c692d7ae4b866fefd8a743a21afdb729da0f39c4`;
original document path SHA-256 `230df191d70caadfeb25820f7682f57139785501112a3da8f6c82f80f556e942`,
original content SHA-256 `6208bbe9a1ef8485ed8ab344e74ebb87fb792aa7d5fd983d00bd394e5ac4a113`.
Historical proof hashes identify the original artifacts, not this edited record.

| Field | Value |
| --- | --- |
| Status | completed |
| Plan | [Web UI replacement](../2026-10-20-plan-web-ui.md) |
| Phase | P3 |
| Depends on | [WEB-012](web-012-library-and-discovery.md) |
| Branch | `feat/web-ui` |
| Work-package commit | `WEB-013: implement exact-publication model and dataset details` (this commit) |

## Read before implementation

Catalog detail/variants, references/manifests/revisions, verification evidence; model/dataset screenshots; exact identity and dataset declaration contracts.

Also read the relevant sections of [architecture](../support/web-ui/architecture.md), [API contracts](../support/web-ui/api-contracts.md), [testing strategy](../support/web-ui/testing-strategy.md), [acceptance matrix](../support/web-ui/acceptance-matrix.md), and [human documentation map](../support/web-ui/documentation-map.md). Load only affected living contracts and ADRs through their indexes. Refer to the [source review](../support/web-ui/source-review.md) for pinned baseline evidence; current git wins over it.

## Scope and implementation requirements

Implement stable repository routes plus exact selected SHA/publication state in URLs. Resolve current separately, then pin all derived panel queries to the resulting pair. Provide Overview, Variants/Dataset details, Files & manifest, Revisions, Integrity and Activity tabs. Switching selection invalidates old requests and does not mix cards/variants/verification from different publications.

Show all existing structured evidence with source/capture/coverage: task/language/license/base model/upstream tags; model format/encoding/role/method/scheme/bits/group size/member paths and bytes/completeness/diagnostics; dataset static configs/splits/features/formats. Keep tags explicitly current or last-observed. Unknown values stay unknown; do not infer parameter count/context/GPU fit/rows from filenames.

Show exact publication ID, full/copyable SHA, generation, timestamp, manifest path/digest and logical file/byte totals from available payloads. Provide a bounded accessible file/manifest table and copyable labelled consumer locators, no raw payload endpoint. Integrity uses existing exact-publication evidence; metadata completeness and API health never substitute. Activity is linked loaded history with explicit extent, not an invented complete audit.

## Unit and component validation

Test identity pinning, race/stale queries, conditional model/dataset fields, unknown versus zero, provenance labels, manifest integer/budget handling and URLs/link protocol safety.

## Integration validation

Exercise current changes, old retained publications, repair same-SHA/new-publication, corrupt/missing catalogs with authoritative manifest inventory, and oversized detail/manifest responses against real APIs.

## Functional validation

Navigate all tabs for model and dataset through Caddy, bookmark an old exact publication, change current, revisit, then remove that publication and verify explicit unavailable rather than latest fallback. Test file table keyboard use and consumer-locator labels.

## Human documentation deliverables

Create repository-details.md explaining all identity/evidence classes and dataset limitations; update consumer links and troubleshooting. Screenshots must come from the actual synthetic functional deployment.

## Acceptance

Each detail page surfaces the available evidence without fabricating metadata or mixing publications, supports models/datasets correctly, and remains useful when supplemental metadata is unavailable.

Historical execution summary: the recorded gate included the retired interface; exact invocation and original proof remain in Git `c692d7ae4b866fefd8a743a21afdb729da0f39c4`.

## Execution notes and blockers

## Completion evidence

Completed2026-10-26, WEB-013, this commit, from parent `dfb706c`. Exact source:
1431 frozen regular inputs, snapshot
`0331b88281ef1fe7a61848062bbbdcfbe4787b6d05ba44abe8a0f01efdfe9e0d`.

- `historical gate invocation (original command SHA-256 `dfe15d4ee16e8207e5ddfe1138f7416950f8e6013a5d77e8aa230bfd51dccdc4`; Git `c692d7ae4b866fefd8a743a21afdb729da0f39c4`)` PASS1608.747s/exit0.
  All8591 backend tests pass;52 unrelated live/NFS/build opt-in tests are
  deselected, with no required skip. historical frontend581 unit and110 mounted Firefox
  tests, web3372 unit and3496 combined component tests, frozen dependencies,
  lint/format/types/contracts, locked base/server/MCP wheel profiles, build,
  two Chromium startup checks and real HTTP/API React read fixture all pass.
  Gate source hashes/modes have no drift. Evidence:
  `/var/tmp/web-013-validation-20o27efw/gate1/strict-gate-result.json`, SHA256
  `5626e32285c81d451208f147246f06db701d2d5ad55279427a0fcf6e49dafa98`;
  log SHA256 `947388991ca4cddc2be77d20b50924393cc41558c54f7c8a8db7b0550d327922`.
- Focused source tests: routes100/facade38, detail components21, recognized
  shell8 and real-ASGI manifest bounds2. The component regression exposed and
  fixed focus loss while a selected reference rejoins. Invalid cached bookmarks,
  route changes, stale responses, same-SHA replacement, generation-qualified
  reports and finite report diagnostics remain covered. Full frontend coverage
  passes; independent preflight3496/0skips reports95.93% lines,91.08% branches,
  94.44% statements and94.03% functions (`component-preflight.json`).
- Installed functional2 PASS309.282s/exit0:39 one-attempt cases,13 per
  Chromium156.0.8078.4, Firefox157.0 and WebKit27.2, built UI through trusted
  TLS/shared Caddy to installed native0.2.22 API. The configured Library link
  performs real SPA navigation; model/dataset six tabs, provenance, exact
  bookmarks, current movement, retained selection, repair, replacement, prune,
  unavailable orphan protection, missing/corrupt adjuncts, local25+13 file
  paging, invalid fragments and keyboard/mobile locator labels all pass.
  Passive bounded observation records162/155/171 trusted GETs,0POST, no
  interception/overflow. All10 explicit owned metadata transitions complete;
  all other full9 identities and source bytes, configuration and original
  metadata inodes are preserved. Operation-store count0. Original browser,
  container, transition thread, API/Caddy roles and endpoints drain normally;
  original five infrastructure pairs stay unchanged, cleanup_unknownfalse.
- Functional evidence: `/var/tmp/web-013-validation-20o27efw/functional2-evidence.json`,
  SHA256 `832e54ddad479863c614676e7f470dab7711250d5231f89b0ca726c2c170d9bc`,
  actual cohort `815f7e14d7e149f99a4645a4ef97ebb4`. It is explicit
  `LOCAL_NFS_METADATA_SIMULATION` with strict synthetic catalog/history/models,
  not live NAS, ingestion or new native/rootless platform acceptance. API runs
  with private network/only loopback; actual installed authentication and
  rendering stay real. [Acceptance ledger](../support/web-ui/acceptance-evidence.json)
  records63 actual test mappings/executions; CATALOG06–08 are completed.
- Matching wheel/UI/image: `/var/tmp/web-013-artifacts-20o27efw/stock.json`.
  Wheel `637e32f1153d538e893a828d0493dbca18fbab48b6f360a9eba3dc07935ea01e`;
  UI manifest `f344ad2564d744ab9c49bef7ad9485f8ddd95f366808e52872e820f49cbfaa5b`;
  image `4e04c3d197e1d2f9096ddc8c7c9ca623296ce6138c4419d26f9148d9030758a5`.
  Source proof `artifact-source-proof.json` matches all1431 hashes/modes;
  only copied project/lock self-version fields project0.2.2 to fixture0.2.22.
  All114 installed module files match. Pinned UBI10micro ancestry/stock Red Hat
  CA foundation passes. Separate actual network-none/read-only UID981 image
  probe confirms Node/nodejs/npm/pnpm/yarn/corepack/uv/pip/dnf/rpm absent and
  the installed UI digest exact (`image-no-node-proof.json`, SHA256
  `8f1d3388f9014f0659aad661073a4b2047defd55d35d089e53b07c3c7840f727`).
- Private tools: fixture `687899c2ca07c7422351c25e3b3ed60825ab2a25a55ca1073f5892664b20cbec`;
  driver `d1cb6f203ff3ab279fd9730314d4693a937307a866833626682a5d49fd565bdf`;
  coordinatorv2 `5a9053eb3f2f628799744a046ff748ee0c634d64e23d715b5509510cc0ff5e3c`.
  Functional1 remains failed4.558s/exit1, cohort6702e6e4ff7c46cea4067b4d2ea5c30b:
  a fixture loop shadowed repository_id before strict manifest construction.
  No service/browser role started; original input/source/workspace and
  `functional1-setup-diagnostic.log` remain retained. The narrow ignored fixture
  fix passes12 host-local strict publication constructions and the fresh run;
  no product source/wheel/UI change or retroactive promotion occurred.
- Human repository-details guide, three actual synthetic screenshots, Library
  navigation, consumer/troubleshooting and API/server/security/discovery links
  are synchronized; docs214/27 pass. INV018/021 and ADR133/145/147 were reviewed
  and amended for exact reference membership, bounded composition, labelled
  locator bases and narrow authenticated routes. No new endpoint, durable format,
  runtime dependency, architectural authority or Caddy authentication gate.

Final bookkeeping/acceptance/human-link regressions:78PASS9.27s; documentation
alignment214 human documents/27helpers PASS. Precommit source preservation
rechecks all1431 frozen hashes/modes and the original CLAUDE→AGENTS symlink;
no drift (`precommit-source-preservation.json`).
