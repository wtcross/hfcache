# WEB-014: Render archived README cards as inert, bounded React content

Interface-only instructions and source references have been omitted from this
retained shared record. Exact original text remains in Git `c692d7ae4b866fefd8a743a21afdb729da0f39c4`;
original document path SHA-256 `5c9b01b5b8c6dd19cd85cc0faf1a133aae151b8f7556a1a4cd34cbbe5f6ea8de`,
original content SHA-256 `11c550b71620c851bb31e69d040416e6160fd9c045a81effd1f3c125ea1998e5`.
Historical proof hashes identify the original artifacts, not this edited record.

| Field | Value |
| --- | --- |
| Status | complete |
| Plan | [Web UI replacement](../2026-10-20-plan-web-ui.md) |
| Phase | P3 |
| Depends on | [WEB-013](web-013-publication-detail-pages.md) |
| Branch | `feat/web-ui` |
| Work-package commit | `WEB-014: render bounded inert archived README cards` (this commit) |

## Read before implementation

Card endpoint/decoder; architecture card/XSS policy; react-markdown primary docs at pinned version; details Overview layout.

Also read the relevant sections of [architecture](../support/web-ui/architecture.md), [API contracts](../support/web-ui/api-contracts.md), [testing strategy](../support/web-ui/testing-strategy.md), [acceptance matrix](../support/web-ui/acceptance-matrix.md), and [human documentation map](../support/web-ui/documentation-map.md). Load only affected living contracts and ADRs through their indexes. Refer to the [source review](../support/web-ui/source-review.md) for pinned baseline evidence; current git wins over it.

## Scope and implementation requirements

Integrate react-markdown/GFM with an explicit reviewed sanitizer allowlist and custom link/image/heading components. Disable raw HTML and MDX, unsafe protocols, embedded script/style/SVG/iframe/form/object and dynamic content. Do not use dangerouslySetInnerHTML or load plugins, fonts/images/scripts from card references. Represent external media as labelled placeholders and rewrite safe relative navigation against exact upstream commit/type identity with no opener/referrer.

Render capture/source/provenance/limited-content status prominently. Provide rendered and sanitized-source views, clearly identifying redaction and derivative content. Hide front matter from the rendered prose only through a safe bounded parser; supported metadata already comes from attributed extraction. Unsupported Markdown constructs degrade to inert text or a clear state, never looser execution.

Enforce finite input/parse/render work, table/code block/heading limits and accessible overflow. A malicious card cannot freeze the page, clobber navigation identifiers, mutate page state, read credentials or call same-origin management endpoints. Rendering errors stay local to the card and do not break operations recovery.

## Unit and component validation

Test hostile Markdown/HTML/MDX, mixed-case/control-encoded javascript/data/blob URLs, attribute injection, SVG/forms, DOM clobbering, deeply nested/tables/code limits, invalid encodings, relative URLs and redacted source view.

## Integration validation

Run real captured cards through API decoders and renderer with normal/partial/missing/oversized/mismatched fixtures. Verify CSP and no-store headers, no unsanitized alternative route, and no GET-triggered payload read.

## Functional validation

In all three engines through Caddy, inspect actual DOM, CSP violations and network requests while displaying hostile cards. Assert zero executable/script/frame/form/external-resource effects and no mutation request. Verify keyboard/link behavior and graceful bounded failure.

## Human documentation deliverables

Complete readme-cards.md: offline provenance, supported formatting, blocked media/links, source toggle, missing capture and explicit refresh, upstream claims versus verified archive evidence. Update security dependencies and examples.

## Acceptance

Useful README content displays safely for model/dataset publications, including hostile inputs, without external requests or execution; source view cannot reveal unsuppressed credentials.

Historical execution summary: the recorded gate included the retired interface; exact invocation and original proof remain in Git `c692d7ae4b866fefd8a743a21afdb729da0f39c4`.

## Execution notes and blockers

2026-10-26 review checkpoint: the first source freeze/build and standalone
0.2.24 installation are retained without acceptance. Read-only review found
an indented fence-like accounting edge against the16KiB code-block promise;
the overall64KiB input cap held, and actual capture rejects that exact form as
unsupported. The UI defense is nevertheless corrected before acceptance:
conservative fence recognition plus an independent parsed-code bound, with new
unit/component regressions. Gate1 was withdrawn through normal SIGINT to its
original owned pytest process (exit2/442.408s,3095 passed before interruption),
not promoted from a partial run. No installed service/browser role had started.
The corrected source receives a new freeze, matching build and full gate2;
original inputs/proofs/prefix remain separate and preserved. No production or
NAS action follows this local test correction.

Corrected source2 is frozen at
`bca43be09412585b0cd67edc456a8eacc8cf6d4d7556efbc401cffb686279fa7`
(1441 inputs), with30 policy and32 renderer component cases passing. Matching
source2 build/image and fresh-prefix install pass. Installed attempt1 stopped
before any service/browser because private CLI dispatch preceded a helper;
only its footer was corrected and the original is retained. Attempt2 passes
Chromium12/Firefox12/WebKit11 cases but remains failed: the final WebKit CSP
assertion observes three inline style elements and one style attribute. Pinned
Playwright source attributes the three elements to its unconditional WebKit
screenshot synchronization; no application inline-style path was found. A new
browser attempt retains all36 DOM/network/CSP cases and the zero-event assertion,
while supplemental documentation captures run only in Chromium without extra
animation/caret injection. No CSP relaxation, event filter or skipped required
case establishes acceptance. Original false flags/normal role drains and both
failed cohorts remain retained. Full gate2 and fresh functional acceptance are
still pending here; no completion is claimed by this checkpoint.

The isolated WebKit diagnostic now attributes the remaining event to native
`select` construction: actual card view has0 events, Operations has1 targeting
its selector, and fresh neutral selectors reproduce it while text inputs,
textareas, options and divs do not. Diagnostic1 completes59.146s with known
normal drain, explicitly not feature acceptance. Scope includes a small
compatibility correction to the two recovery selectors: labelled native radio
groups, unchanged state/handle/namespace/API logic. Nine component tests and
whole types/lint pass. The CSP and full required browser assertion remain
unchanged. Source3 receives a fresh full gate/build and real three-engine run;
all prior evidence remains retained.

Source3 installed functional4 passes all36 one-attempt cases through actual
Caddy/API in Chromium, Firefox and WebKit (235.043s). All90 CSP checkpoints are
zero;158/146/158 trusted GETs and0 POSTs, with unchanged archive/source/configuration
bytes and normal original-role drain. The Recovery radios preserve keyboard
selection and the unsaved original handle without network or submission effects.
Three unmodified Chromium screenshots now illustrate the human README guide;
documentation alignment passes215 human documents/27 helpers.

Gate3's command session ended143 during Python tests at85%, without a final
gate result. No source drift or test failure was observed; its cause remains
unproven and the partial run is not acceptance. Original log and interruption
facts remain under `/var/tmp/web-014-validation-xowemz0k/gate3/`. The identical
full gate4 runs in an owned detached session against the unchanged source3 freeze
`4b336cd30202a80445d7b3d4c0d47416048070c7c252710d1e1620d088247798`.
Completion and the acceptance ledger remain pending that actual full result.

## Completion evidence

Completed2026-10-26, WEB-014, this commit. Evidence directory:
`/var/tmp/web-014-validation-xowemz0k` (`E14` below).

- Implementation: lazy closed CommonMark/GFM/sanitizer rendering, exact sanitized
  source, publication/digest provenance, inert media, immutable upstream links,
  trusted heading IDs, finite lexical/AST/code/table work and local error handling.
  No new endpoint, payload read, automatic refresh or backend dependency.
  Thirty policy unit cases,32 renderer component cases,21 detail cases,9 recovery
  cases and2 license cases pass focused checks; whole frontend types/lint pass.
  The license inventory checks the actual complete frozen production closure;
  pinned MIT/ISC dependency notices and production audit (zero advisories) pass.
- Source3 freeze:1441 regular inputs,
  `4b336cd30202a80445d7b3d4c0d47416048070c7c252710d1e1620d088247798`.
  Matching build under `/var/tmp/web-014-artifacts-source3-xowemz0k`:
  image`sha256:8b7a960893331bc1c7660b4439d652a2aa662abc547b0e3abaa570469f9025f7`,
  UI manifest`2cdd822c89e672497c3b7dcc31c4b2e447d3fa3bc958879b84c1ea1b82b11540`,
  wheel`11dbffd1b0499e3239bab80ed6cef371a5cb0aac69a3546ecde1ea0d0bea79af`.
  `E14/artifact-source-proof-source3.json` (SHA176a82a0…) rejoins every frozen
  hash/mode and all1447 projected files, allowing only fixture self-version
  metadata0.2.24; canonical project0.2.2 is unchanged. Installed114 Python modules
  match under `/opt/hfcache-web014-source3-runtime`; no release selector changes.
  Actual image ancestry/stock CA and UID981/read-only/network-none probe prove
  pinned UBI10micro, matching UI and absent Node/package managers (proofSHA5dc12122…).
- Full command `historical gate invocation (original command SHA-256 `dfe15d4ee16e8207e5ddfe1138f7416950f8e6013a5d77e8aa230bfd51dccdc4`; Git `c692d7ae4b866fefd8a743a21afdb729da0f39c4`)` passes gate4
  exit0/1465.321s with changed_source_files[]. All8591 backend cases pass
  (52 unrelated opt-in deselections),581 historical frontend unit/110 mounted Firefox,
  3404 web unit and3561 combined unit/component cases;96.01% line/91.29% branch
  coverage. Locked wheels in all three supported profiles, format/lint/types,
  contracts/licenses, strict metadata/auth fixtures, production builds,2 built
  startup browser cases and the real API React fixture pass. No required skip.
  `E14/gate4/strict-gate-result.json` SHA
  `5a6aa08f79d270c1e0582baf8548e864ca3bdaf456fc4c2b79776c5a99cc77ab`;
  logSHA`54ed64abb387c53b10ef9ce76add2f4e30691744a81a7bbf21abc295e617b7cb`.
- Actual functional command:
  `rtk proxy python3 -I -B .scratch/web-008-call-guest.py --script /home/webfixture/web014-source3-inputs/web-014-run-owned-functional-source3.py --log /var/tmp/web-014-validation-xowemz0k/functional4.log`.
  Functional4 exits0/235.043s, case`0da118a0a6b04af0b38c209fbb81967b`;
  `E14/functional4-evidence.json` SHA
  `a02db2f96d02ea509831a850db5c9dba1a681e20af9df616d33ff8374b844d2a`.
  All36 one-attempt cases pass:12 each Chromium156.0.8078.4, Firefox157.0 and
  WebKit27.2. Real capture/CatalogWriter/API decoders/built UI/shared Caddy/trusted
  TLS exercise11 genuine capture states, exact source/redaction, DOM/links,
  bounded refusal, unavailable publication, keyboard/mobile and Recovery radios.
  All90 CSP checkpoints and executable/media/dialog/popup/error observations
  are zero;158/146/158 trusted GETs,0POST, no interception or skipped required case.
  Full9/source/configuration bytes remain unchanged, operation store0/canary absent;
  original browser/API/Caddy roles drain normally, cleanup uncertaintyfalse.
  Scope is explicitly `LOCAL_NFS_METADATA_SIMULATION`, not NAS/ingestion or fresh
  complete native/rootless platform acceptance. API private networking has onlylo.
- Retained failures: gate1 withdrawn after the code-budget review; source2 gate2
  passed1614.226s but does not qualify source3. Functional1 failed before any role
  due to fixture footer ordering; only that private footer changed. Functional2/3
  remain failed35/36. Actual pinned Playwright screenshot source and separate
  diagnostic-only cases isolate screenshot style insertion and native WebKit
  select construction respectively. Supplemental documentation images are captured
  only by Chromium; all36 required assertions and unfiltered zero-CSP observations
  remain. Recovery uses tested native radios with unchanged handle/API semantics.
  Diagnostics1/2 (59.146s/70.113s) are collection evidence, not feature acceptance.
  Gate3 ended143 without a result at85% Python tests; its original interruption
  evidence is preserved. Gate4 repeats the full command on identical source.
- Human guides: README cards, repository details, Operations radio usage,
  troubleshooting and navigation; living development/security/discovery contracts
  and INV021 align. ADR142/143 amendments link new decision155. Actual final
  screenshots (synthetic data) match functional4: renderedSHA6ad22bb8…,
  datasetSHAf748d355…, mobile sourceSHAdca74965…. Documentation alignment passes
  215 human documents/27 helpers after captions. No production/NAS/installed predecessor interface,
  rollout, merge, push or tag action.

CARD10–12 now map actual unit/component/integration/functional evidence in the
acceptance ledger; prior cases and failed/interrupted/diagnostic outcomes remain
preserved. Plan/current select WEB-015; completed progress and Operator handoff
record the source/build/functional scope. Final bookkeeping command
`uv run --locked --extra server --extra mcp pytest tests/unit/test_web_plan.py tests/unit/test_docs_alignment.py tests/unit/test_docs_config_contract.py tests/unit/test_docs_migration.py`
passes78 cases/12.86s; all frozen source hashes/modes remain exact. The final strict plan-wide gate remains later
scope; historical frontend retirement is not authorized by this package's result.
