# WEB-003: Make the browser wire boundary precisely typed and validated

Interface-only instructions and source references have been omitted from this
retained shared record. Exact original text remains in Git `c692d7ae4b866fefd8a743a21afdb729da0f39c4`;
original document path SHA-256 `f357faa949fa5d98a848ef2e0bcd8b88c359892fd9d38bef2c7c69ff75526c69`,
original content SHA-256 `7fb71903f7d1b97fb3b4232d38a4f3904e005e05ad3ffefd7b58cbb563efb3a9`.
Historical proof hashes identify the original artifacts, not this edited record.

| Field | Value |
| --- | --- |
| Status | completed |
| Plan | [Web UI replacement](../2026-10-20-plan-web-ui.md) |
| Phase | P0 |
| Depends on | [WEB-002](web-002-strict-frontend-and-gates.md) |
| Branch | `feat/web-ui` |
| Work-package commit | `WEB-003: validate generated browser wire contracts` |

## Read before implementation

src/hfcache/api/models.py, app.py, catalog.py; domain/catalog payload models; current OpenAPI and ReadResponse contracts; web workspace.

Also read the relevant sections of [architecture](../support/web-ui/architecture.md), [API contracts](../support/web-ui/api-contracts.md), [testing strategy](../support/web-ui/testing-strategy.md), [acceptance matrix](../support/web-ui/acceptance-matrix.md), and [human documentation map](../support/web-ui/documentation-map.md). Load only affected living contracts and ADRs through their indexes. Refer to the [source review](../support/web-ui/source-review.md) for pinned baseline evidence; current git wins over it.

## Scope and implementation requirements

Define the typed response/payload registry needed by each UI route. Resolve generic Envelope data and x-catalog-payload schemas without changing stable ReadResponse/capabilities/operation wire shapes unnecessarily. Generate types/runtime schemas mechanically from authoritative models, with independent expected fixtures and checked regeneration drift. Add runtime decoders from unknown, discriminated state models, safe large-integer handling, limits and domain-error preservation. Typed ApiProblem handling must distinguish transport errors from failed domain Envelopes.

Build a same-origin REST client with explicit read versus mutation paths, no automatic mutation retry, bounded read body collection, AbortSignal, validated relative links, and consistent request metadata. Query keys include auth/authority/archive and exact publication identity. Do not cache passwords or expose generic arbitrary-target fetch. Define typed contracts for forthcoming config/card/host payloads only after WEB-001's contract decision; never pretend unimplemented endpoints return data.

## Unit and component validation

Golden tests cover valid and malformed wrappers, unknown schema, missing fields, false/zero/null distinctions, extra forbidden keys, failed HTTP-200 Envelopes, UTF-8 and large integers. Exhaustively test client URL/path construction and no mutation retry.

## Integration validation

Round-trip actual Python-serialized schemas through TS validators. Call real baseline REST routes with the client on an owned ASGI/HTTP fixture. Prove schema regeneration drift and independent incorrect wire fixtures fail.

## Functional validation

Mount a real React status/read view against the owned real API and verify failed/unknown payload presentation. This may use temporary shell routing until WEB-005; report that limitation.

## Human documentation deliverables

Update API/schema and development references for generated contracts, error taxonomy and bounds; update troubleshooting language for unavailable versus failed reads. Do not expose internal type-generation steps as user workflow.

## Acceptance

No UI route relies on a free-form any Envelope or blind cast; actual backend payloads validate; error and integer handling are tested; old wire schemas and base client behavior remain compatible.

Historical execution summary: the recorded gate included the retired interface; exact invocation and original proof remain in Git `c692d7ae4b866fefd8a743a21afdb729da0f39c4`.

## Execution notes and blockers

Started after completed WEB-002 commit `107eca3` and its corrected full strict
gate. Read-only surveys preserve the baseline route/serializer/schema inventory
at `.scratch/web-003-survey/` and exact native numeric-token probes at
`.scratch/web-003-native-json-survey/`; these are design evidence, not completed
wire acceptance. Node and the actual sandboxed Chromium preserve JSON numeric
source tokens before field validation; unsupported source context will refuse.

The implementation uses pure authoritative Python projections and a route/mode
registry, an audited normalized schema IR, mechanically generated reconstructing
TypeScript decoders, explicit semantic checks and native bounded JSON parsing.
Unknown schema constructs or unaudited validators fail generation. No new runtime
parser dependency or stable wire change is intended. Requests keep omitted/null
distinctions; serialized responses require fields rather than fill defaults.
Root owns contracts/docs/gate integration, with separate collaborators owning
Python authorities, frontend boundary and independent adversarial/real-API React
fixture validation. All share this work-package commit. The temporary built
read fixture is permitted before WEB-005; it cannot claim Caddy/Basic/installed
platform acceptance. No production or unrelated state is touched.

Registry availability is deliberate: runtime DTOs/types cover implemented
baseline routes and their real serializers. The accepted future config/card/host
design remains normative in WEB-001's execution contract; exact Python DTOs and
generated types join the registry in the owning WEB-006–010 implementation,
alongside actual serializer/request and functional evidence. A second invented
planned-response registry would have no executable authority and must not imply
that those endpoints exist. This timing clarification preserves the final typed
boundary requirement for every new route; no fetch method targets a missing API.

Focused checks so far: 60 root catalog/manifest/Unicode tests pass, with 99.31%
line/94.79% branch/100% function coverage in
`web/.artifacts/web-003-root-semantic-coverage-1/`. Official Unicode16 checks cover
all 19,965 normalization rows and 1,557 full/common casefold rows; exact source
bytes and license hashes are pinned. PythonUCD16 differs from NodeUCD17, so a
bounded exact table implementation replaces native normalization as authority.
Independent review found JS `$` accepting final LF in three catalog checks;
true full-match comparison and LF/CRLF negatives repair that false accept.
Combined strict TypeScript passes. Gate/safe-help/Unicode controls pass 107 tests
after correcting the read helper's public-help identifier leak (the earlier run
had 101 passing/one audience-only failure, no runtime help access). Python registry
direct checks pass 31 tests; independent parser/identity checks pass 97. These
are interim evidence, not completion of the full strict or real-API browser gate.

Final preflight freezes 79 source/contract/test inputs against parent `107eca3`:
`.scratch/web-003-final-source-inputs.json`, manifest SHA256
`0a90cd371f24384c470616d1c4648f9c4a2111b39bec4d8d6243080547b1bd85`,
source-set SHA256
`16480443c76be5ab4cf3bbc330233f4da78a873b84451080fc7e6fcd45a23366`.
Only this task, plan, current selector and progress bookkeeping are excluded;
the source manifest is verified again before committing. At that preflight,
full-gate acceptance remained pending; the completed run below now supersedes it.

The original-model corpus now contains 271 serialized positive examples and
2,000 independently Python-rejected mutations across all 118 definitions. Direct
Python corpus/registry checks pass 36 tests; the combined root wire roundtrip
selection passes 90. Six independent literals extend the browser corpus to 277.
Both actual HTTP profiles pass seven browser checks each, with four independent
incorrect wires per profile. `.scratch/web-003-independent-evidence-v3978hph/`
retains source/artifact manifests and the final `.scratch/web-read-fixture-uxjzt7k_`
run: actual API owner2115825, wrappers2115862/2116098 and Chromium2115881/2116112
all exited, with exact browser/API pool/lifespan/listener drain observed. All five
earlier failed fixture workspaces remain intact; their startup defects and wrong
test expectations were corrected without replacing real route behavior.

The final frontend preflight passes 2,744 combined tests, zero skips/pending/todo,
including original-model positives/negatives, independent adversaries, real
component behavior and all official Unicode vectors. Coverage is 95.85% lines,
92.94% branches, 94.83% statements and 93.93% functions, including generated code.
`web/.artifacts/WEB-003-frontend-evidence.json` SHA256
`ff8e99ae0f4c13e1c1b785862b01e4bd5615a1dfea41056a2144d1a0c80a6e27`
records exact reports/source hashes and the four test-only callback formatting
changes after that coverage run. The strict gate reruns those exact final files.
Whole frontend lint/types, strict rejection fixtures and both drift checks pass.
An earlier root preflight exposed empty-object union inference and nonconverged
generated formatting; explicit union generation and bounded formatter convergence
correct them without casts or lint suppression.

Python printability now also uses 737 pinned exclusion ranges, exhaustively
compared with Python across all 1,114,112 points. This closes browser Unicode17
assignment differences for compatibility-only archive-root input; the UI exposes
no initialization method. Final Unicode-data SHA256:
`c615ef0f65133fb3791ef9d8bf0acb816edabc0e40335e0240bd96b76e73171a`.
Client prefix validation preserves the existing server's normalized Unicode and
punctuation grammar; even a permitted double-leading slash remains an inert
same-origin path. Exact operation links are compared, never followed as targets.
Receipt observations refuse backward states/timestamps and changed creation
identity while allowing skipped intermediate polling states. Focused independent
root-semantics audit passes 61 TS/52 Python checks; 85 client adversaries pass.

A read-only follow-up probe confirms two **existing server** prefix defects for
the serving task to reconcile: non-Latin1 configured prefix causes the baseline
acknowledgement's raw Location encoding to fail, and an accepted double-leading
prefix produces a protocol-relative MCP redirect. No application/lifespan,
persistence, network or production effects were used. Evidence:
`.scratch/web-005-prefix-survey/results.json`, SHA256
`f56e007c9fb6cf3870e231fa07bf31dc17a22e6eb88f2703d202fdf93044a062`.
This package's client constructs fixed same-origin URLs and never follows those
links as targets; it changes no server wire or redirect behavior. WEB-005 must
resolve and functionally test the server's prefix/header contract before its
routing acceptance. Its current fixture profiles remain empty and `/management`.

## Completion evidence

Completed 2026-10-20, WEB-003, this commit, parent `107eca3` on `feat/web-ui`.
Historical execution summary: the recorded gate included the retired interface; exact invocation and original proof remain in Git `c692d7ae4b866fefd8a743a21afdb729da0f39c4`.
exits **0** on the final frozen source. Log `.scratch/web-003-final-gate.log`
SHA256 `0beabaea07f3be5ad95389c40275cd67598d076776cf263d70b269f11396e0a5`.
The independent collection/verification record
`.scratch/web-003-final-evidence.json` SHA256
`f0e2e73eff6c5892d706813d576294086f4ed4ca16b03110875117ed2c46fcce`
retains exact artifact hashes, report counts, coverage and process absence.
All 79 inputs still match the source manifest above after the gate; no unexpected
source input joined the change. Only the four listed bookkeeping files change
after that freeze, followed by the documentation/plan checks before committing.

### Final gate and functional result

- Lock/sync, Python export drift, Ruff format/lint, Pyrefly and documentation
  alignment pass: 197 human documents and 21 safe-help helpers.
- **5,452 Python tests pass**, 52 explicitly opt-in tests deselected, 706.13 s.
  Wheel/sdist build and all three locked base/server/server+MCP installation,
  import/help/version checks pass. No required check is skipped.
- historical frontend lint/style/types/build, **572 unit tests**, zero skip/cancel/todo, and
  **110 mounted Firefox tests** pass. This is the retained controlled historical frontend
  boundary fixture, not a new production PAM/API claim.
- Frozen web install, generation drift, lint/types and actual negative strictness
  fixtures pass; **2,718 unit / 2,744 combined component tests** pass with zero
  skip/pending/todo. Full-source coverage remains **95.85% lines, 92.94% branches,
  94.83% statements and 93.93% functions**, including generated decoders.
- Production shell build is 155,361 bytes, 47,654 gzip JavaScript bytes. All 274
  locked npm packages and pinned Unicode16 source/license notices verify offline.
  No new Python or JavaScript runtime dependency is introduced.
- **Two sandboxed Chromium built-shell tests** pass, zero skip/retry. Owned PID
  2139228 and its HTTP listener close explicitly; the PID is subsequently absent.
- The required source-built **real HTTP/API React fixture passes 14 browser
  tests**, seven each at empty prefix and `/management`, zero skip/retry.
  Final workspace `.scratch/web-read-fixture-c8w65s3p/` retains real status/version/
  capabilities and failed-inspection reads, actual policy503/access401 responses,
  labelled post-service unknown-schema corruption and 277 original examples plus
  four independent incorrect wires per profile. API owner2139391, Node wrappers
  2139433/2139655 and Chromium2139445/2139669 all exit; exact browser close and API
  pool/lifespan/listener drain are observed, and all six final-run PIDs are absent.

Exact final reports and hashes:

- `web/.artifacts/unit-1tOY9t/report.json`:
  `6f1f22e627ed1527b424956bf07726a019005992b7cbeb4ca991ee411ff0ebaf`.
- `web/.artifacts/component-mYj6EU/report.json`:
  `30583be5a79b5c9f3d70c0080eeb90e091094a713d398dfdfee6252830dc57fe`.
- Its `coverage/coverage-summary.json`:
  `48099df325c8822cb07ebb8b89b653018220dc21dc26c39866daa8203eaa1ba3`.
- `web/.artifacts/browser-Wma80Z/report.json`:
  `bacc03ff7bdc13bb0f16c3f5cf42ac5f0c3d3597929d56a7a02f8f8339e00080`.
- `.scratch/web-read-fixture-c8w65s3p/root/browser/run-PzytXc/report.json`:
  `455768f589c28984194115d9a74c52858b0cd7ac1e23e8cab8f1a9690a978da2`.
- `.scratch/web-read-fixture-c8w65s3p/prefixed/browser/run-dgF54N/report.json`:
  `a439cde3c7269a08e227608e03d23e1f5ce9d2aafaa31d59204691034cecba85`.
- Final real-API `SUMMARY.json`:
  `f8721256e13ffbd8d7b247c62a69fdeaf9671840ca96f3187ce4a89da4abf20b`.
- Wheel `a7503c0f55a74e88f4c4029cd91ef6cefd353352bda109d7e61f437e67997519`;
  sdist `a056cfcd524a007e8a6695a9b4cb198d30f3d8c16df2eb539b034539549e7c6d`.
- IR `7d278e29e1e8c70d57c4bf6662465f37811d99c19b29096df44b38cee88fe1d6`;
  generated TS `477cb6ccd9c70960f802aeddaa1f8cc493f7af98d25cc61c73b1a62a4553908a`.

### Test ownership, contract review and handoff

Python nodes in `test_wire_contracts.py`, `test_web_wire_contracts.py`,
`test_web_wire_corpus.py`, `test_web_wire_integration.py`, `test_web_unicode.py`
and `test_check_web_gate.py` cover exact registry/modes, source auditing, exported
drift, original serializers, incorrect wires, protected fixture ownership/local
mount proof and required-stage refusal. The frontend's exact named nodes are
retained in the reports above: `original-models`, `wire-json`, `wire-semantics`,
`wire-adversarial`, `api-client`, `client-adversarial`, `bindings`, catalog/
manifest/Unicode semantics, fixture ownership and `StatusReadView` suites. Real
functional nodes are `web/test/read-api/read-api.spec.ts` in both prefix profiles;
they exercise the built real component/client and actual API, not mocked reads.
All required malformed-number/key/Unicode/schema/identity, failed-domain/HTTP,
transport/abort/timeout and no-replay outcomes pass. Earlier failed workspaces,
preflight diagnostics and original oracle errors remain recorded above.

Reviewed INV-001/002/003/005/006/007/010/013/014/018/019/021, AD-01/12/14/15/16/17,
FW-01–04 and relevant decisions 14/15/114/118/119/123/133/137/140/143.
[Decision145](../../../adr/decision-145.md) records exact generation/numeric/
Unicode/client choices; ADR137/143 explicitly link the amendment. INV021 is added.
No durable format, original server wire, permission, archive/Hub authority,
existing operation handle or CLI/MCP behavior changes. Exact future config/card/
host DTO timing remains as reconciled in the execution notes, with no invented
endpoint behavior.

Human API/schema/development/script references and UI troubleshooting/navigation
are updated alongside the implementation. Documentation, plan/dependency/ADR,
link and whitespace checks pass after completion bookkeeping: **100 tests** in
10.59 s and documentation197human/21helpers. The first bookkeeping check caught
one incorrect relative progress link (90 passing/one failure); that record-only
link is corrected, and both failed/corrected logs remain under `.scratch/`.
No frozen source changes. The completed
[progress entry and handoff33](../../progress.md#web-ui-replacement-2026-10-20),
parent plan lifecycle and [current selector](../current.md) advance to WEB-004.
All 95 feature cases remain pending in their owning packages. This permitted
temporary read fixture is source-only: **no Caddy, Basic, installed native/rootless,
NFS/NAS, production or historical frontend-retirement acceptance** follows from it. Known
baseline prefix fixes belong to WEB-005. Original production state, guards,
stores, handles, candidates, backups and five unrelated guests remain untouched;
no remote publication, rollout, replay or cleanup is authorized.
