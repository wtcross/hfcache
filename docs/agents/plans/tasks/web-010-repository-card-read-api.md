# WEB-010: Expose a bounded exact-publication card read

Interface-only instructions and source references have been omitted from this
retained shared record. Exact original text remains in Git `c692d7ae4b866fefd8a743a21afdb729da0f39c4`;
original document path SHA-256 `9f5e40ff90e46110503ffa235bf8da05d70768e455a6c32d8788938ca33b71cd`,
original content SHA-256 `8f05d236f59a4d979ac851a753bf073327e4ca2d8ac543c2cdbf0840765e0469`.
Historical proof hashes identify the original artifacts, not this edited record.

| Field | Value |
| --- | --- |
| Status | completed |
| Plan | [Web UI replacement](../2026-10-20-plan-web-ui.md) |
| Phase | P2 |
| Depends on | [WEB-009](web-009-repository-card-capture.md) |
| Branch | `feat/web-ui` |
| Work-package commit | `WEB-010: expose bounded exact-publication card reads` |

## Read before implementation

API metadata leases and identity checks; card model/layout; generated wire schemas; exact publication routes and API contract.

Also read the relevant sections of [architecture](../support/web-ui/architecture.md), [API contracts](../support/web-ui/api-contracts.md), [testing strategy](../support/web-ui/testing-strategy.md), [acceptance matrix](../support/web-ui/acceptance-matrix.md), and [human documentation map](../support/web-ui/documentation-map.md). Load only affected living contracts and ADRs through their indexes. Refer to the [source review](../support/web-ui/source-review.md) for pinned baseline evidence; current git wins over it.

## Scope and implementation requirements

Implement only the narrow exact SHA/publication card GET. Validate all identity segments and authoritative retained publication membership before returning a card adjunct. No current fallback on missing/pruned/repaired identity, no arbitrary file/URL, no payload open, lock, network, credential resolution, write or refresh from GET.

Return independently versioned card states, bounded sanitized Markdown/source provenance, capture time/presentation version and diagnostics. Missing capture/README are explicit normal states; malformed schema/identity or exhausted budgets are classified failures, not empty success. Preserve metadata pool/lease lifetime through encoding/stream completion and disconnect. Enforce JSON encoding/response maximum before headers and no-store/nosniff/authentication. Add precise schema registry and runtime decoder coverage; source view exposes only the sanitized derivative.

## Unit and component validation

Test identity/type/path grammar, missing/invalid/corrupt adjuncts, retained versus vanished membership, state serialization, byte bounds, redaction and decoder unknown versions.

## Integration validation

Exercise real authenticated GET with REST reader/writer/Basic and denied MCP credentials. Instrument filesystem/network/locks to prove the read touches only allowed metadata and remains bounded under slow clients and disconnect.

## Functional validation

Through Caddy load exact card data for model/dataset and all unavailable states, switch current/repair/prune fixtures mid-observation and prove no silent fallback or mixed publication content.

## Human documentation deliverables

Update API matrix and schema with mode/authority/effects/status/bounds, plus human guide explanations of not captured, missing README, unsafe/oversized card and vanished publication.

## Acceptance

An authenticated browser can obtain only the bounded sanitized card for the requested retained publication, without changing archive state or reaching the Hub; all unavailable/error cases are distinguishable.

Historical execution summary: the recorded gate included the retired interface; exact invocation and original proof remain in Git `c692d7ae4b866fefd8a743a21afdb729da0f39c4`.

## Execution notes and blockers

Retained source1 validation checkpoint: backend79 card tests pass, query coverage100% and
model96% (combined98%); surrounding156 regressions and71 wire/corpus checks pass.
Frontend2879 unit tests/types/lint pass; human docs211/helpers27 validate. Source
is frozen at1388 regular inputs, snapshot
`1dbdb947b8cb2579c64aebd7bd9baf2a71742b63400112a30973b18f5400e700`.
Strict gate1 failed three independent REST route-inventory assertions (8577 pass,52 unrelated opt-in deselections). Runtime acceptance remains valid; only the three independent test inventory files changed after that failure, and181 focused parity/security/card tests now pass. Source2 is frozen for required gate2; no completed acceptance label is inferred yet.

Installed application functional2 passes46.607s with six one-attempt Chromium
cases, all ten publications and actual typed ApiClient reads through real Caddy.
All49 browser requests are GETs at the exact trusted origin. Ordinary and error
states, current/repair/prune reference transitions and no-resurrection behavior
pass; independent whole-file/metadata inspection and normal process/container
drain pass. Only the external storage/mount-table/local-lock seam is simulated;
no native/rootless platform or NAS claim. The private probe bundles the actual
canonical client and uses normal browser Basic authentication, without fake
transport, route interception, extra server or application asset changes.

Matching stock shared API/UI image
`sha256:84b929bca9cd57bfc393920ccea71cd5884e3ed7d38251890097fd6bda274908`
passes pinned UBI10 micro/no-runtime-Node foundation checks. Installed114 package
files match the fixture0.2.14 wheel; there is no release selection. Evidence is
`/var/tmp/web-010-validation-p3visvrb/`; functional raw copy SHA256
`a6c2c342df9a2306196cf89bfe2612f106cb88f7d2266a178f4f1414c90bae23`.
The first build invocation used an older host Python and failed before staging;
the corrected pinned interpreter build passes. Original functional1 passed its
first two cases but its private closed-path URL helper rejected the intended
negative query before sending it. That whole run remains false and normally
drained; a fresh cohort with explicit negative-query construction passes. No
product source or hardening change was needed. Original failed local fixture
smoke inspected a nonexistent exception accessor; corrected local smoke and
state transitions pass without a listener. All earlier evidence remains retained.

## Completion evidence

2026-10-26, WEB-010, this commit; parent `c51cc5b`. CARD07–09 are complete.

- `historical gate invocation (original command SHA-256 `dfe15d4ee16e8207e5ddfe1138f7416950f8e6013a5d77e8aa230bfd51dccdc4`; Git `c692d7ae4b866fefd8a743a21afdb729da0f39c4`)` exits0 in1406.731s.
  8581 Python tests pass (1125.13s);52 unrelated opt-in cases are deselected.
  581 historical frontend unit/110 mounted Firefox,2879 frontend unit/2939 combined component,
  strict lint/types/schema export, three locked wheel profiles, both built-shell
  browser checks and14 real API browser cases pass. No required skip/retry.
  Human docs211/helpers27 pass. Source1388 hashes/modes remain unchanged at
  `71e7056b49adf28d59c81ac602233d009ac6425566dd93c0d84402dcbefec30d`.
  Result/log are `/var/tmp/web-010-validation-p3visvrb/gate3/`; log SHA256
  `c92ef059be06c06abdb102f3d9173f5ff6d11d99689d78a9af6c9838aebc65b3`.
- Focused79 card tests cover strict states/bounds, sentinel/ref/manifest/tree
  rejoin, retention races, reader/writer/Basic authentication and MCP REST401,
  hostile/no-payload access, source/storage/work/encoding refusals and actual
  ASGI slow-send/cancellation lease retention. Query coverage100%, model96%,
  combined98%; the remaining defensive record bound is unreachable under the
  tighter individual bounds, not bypassed for a coverage test. Surrounding156
  regressions,71 export/corpus tests and181 final parity/security/card checks
  pass. Actual executable nodes and observations are in the acceptance index.
- Installed application functional command:
  `rtk python3 .scratch/web-008-call-guest.py --script /home/webfixture/web010-inputs/web-010-run-owned-functional-v2.py --log /var/tmp/web-010-validation-p3visvrb/functional-card-read2.log`.
  Exit0/46.607s, six one-attempt Chromium156.0.8078.4 cases. Built Basic UI,
  trusted real Caddy, installed API and the actual canonical typed ApiClient
  prove ten publications spanning all seven card states plus future-schema
  refusal. Exact current/repair/prune transitions never fall forward or revive
  orphan cards. All49 observed requests are GETs at the trusted origin. Full
  source/card bytes and metadata remain unchanged except explicit toy ref
  transitions. The API actually has onlylo in a distinct private namespace with
  AF_UNIX-only restrictions. Repository-code canary remains absent. Original
  browser/container/API/Caddy roles drain normally and original five infrastructure
  pairs remain unchanged. Storage is explicitly LOCAL_NFS_METADATA_SIMULATION,
  not native/rootless platform, production or NAS acceptance. No renderer claim.
  Local evidence SHA256
  `a6c2c342df9a2306196cf89bfe2612f106cb88f7d2266a178f4f1414c90bae23`;
  guest result `/home/webfixture/web010-runtime/RESULT-009a47cb0a62416b85f7cc94f0dc7512.json`
  SHA256 `0e9f11209973d39565b0f9fcf3911eefb539a7163c2f33f84d91d05999547c03`;
  browser report `c2579ff10e078cd3938c7ba41b56b7fc3ea5c0db57b62ff49ebfdfcea4804e23`;
  independent inspection `8ef702f9d8d622b7fe2a6922c4b85f799d77d142f81f7e7d414b44de5c0277df`.
- Private fixture SHA256
  `7b78935f5e0471017125802e5c4dc2bf6157c97baa9e91123e9fe7fb95b85237`;
  browser-v2 `1344294f96d22f0615f9a690a5c9f927600e0a580462e1a98fbe65cd3d1b5177`;
  coordinator-v2 `3a33ec0e511cc96532ef07245d48ee180884cbcdb2af241ff6b462586f7521f5`;
  unshipped actual-client IIFE `d0934485dffbd929fb913953ad07cb5dde4562fa7fa1fe369a89240ed3c11734`.
  It uses normal browser authentication and actual fetch; no route mock,
  second frontend server or immutable application asset edit is introduced.
- Stock build exits0/63.703s; artifact identities are in
  `/var/tmp/web-010-artifacts-source1-1a6d31530ff7/stock.json`.
  Wheel0.2.14 SHA256
  `84ee3db33836dc77aa28fd5739d75c000cae405daa279ca1f372d6a11b736204`;
  UI manifest `f7f1002ba9450f10957e2a2694d1aa7087e4ce74613c7fad1c8dd2a99a179c77`;
  UI tar `af86858d492239251433bda2adfd1431696b4dcd0f43da49c39f5dba49b63ab3`.
  Shared image `sha256:84b929bca9cd57bfc393920ccea71cd5884e3ed7d38251890097fd6bda274908`
  passes actual pinned UBI10 micro/no-Node foundation audit.114 installed modules
  equal the wheel. Version0.2.14 is a two-TOML-field throwaway projection, not a
  release; rootless0.2.15 is only a builder intention, not installed acceptance.
  Installed source1 differs from final source3 in exactly four independent test
  inventory/count files; all1384 other regular hashes/modes match. Explicit
  source3 artifact reuse proof retains both identities; the original source tar
  has its original inventories and is not a release candidate.
- Failed build1, local smoke, functional1 and strict gates1/2 remain failed and
  retained. Gate1 missed independent REST inventories; gate2 reached its final
  browser test but retained the old347 expected corpus count instead of350.
  Only independent test data changed. Both prefixes passed directly after the
  correction, then the full gate3 passed. Functional1 stopped at its private
  closed-path URL constructor before the negative query; normal drain is proved,
  and no transition-completion flag from that failed run establishes acceptance.
  New fixed-negative-query cohort2 supplies the accepted evidence above.
- Human README provenance/read procedure, API matrix/schema/error/budget,
  discovery/security/navigation and ADR142/INV018 are synchronized. INV002/005/
  018/021, ADR108/125/134/137/142/145 and framework constraints are reviewed;
  no new dependency, durable state format, CLI command, MCP tool, capability
  field or mutation route is introduced. Synchronous decoding checks structure;
  every actual typed card read awaits native digest verification and exact binding
  before exposure, including abort races. Relevant existing contracts remain.
  See completed progress entry and Operator handoff. Next: WEB-011. No production,
  NAS, installed predecessor interface, rollout, merge, push or tag action follows this completion.

## Retained validation checkpoints

The following are earlier outcomes, superseded for completion only by the actual
green gate3 above. Their failed results and original artifacts remain unchanged.

Source2 checkpoint: snapshot
`fedf614103d1587df2aabf1d69b30a261fdcded9b55ee70a530055a8ed8be185` replaces only the three independently reviewed test inventories;
all other1385 regular hashes/modes, including every runtime/browser/packaging
input, remain unchanged. Explicit artifact reuse proof is
`/var/tmp/web-010-validation-p3visvrb/source2-test-only-artifact-reuse-proof.json`.
The original source tar retains its original inventories and is a disclosed
throwaway fixture, never a release candidate. Strict gate2 remains required.

Gate2 result: exit1 in1400.39s, all1388 inputs unchanged.8581 backend tests,
581 historical frontend unit,2879 web unit/2939 combined component, three wheel profiles,
strict checks and built-shell browsers pass. The final real-API browser fixture
stops on its independent old expected count347 while all350 original serialized
models validate and all4 negative wires refuse. Six other root-prefix cases
pass; nonempty prefix was not reached in that failed run. The old run remains
failed and retained at `.scratch/web-read-fixture-lv0awbkh/`. Only that independent
browser test expectation is being corrected, then both prefixes and full gate3
must pass. No runtime/application source correction is required or claimed.

2026-10-26: the one-line independent browser count is corrected350 after actual
`model_corpus()` confirmation (350 originals/4 incorrect). Both real-API fixture
prefixes pass7/7 without skips/retries; APIs/listeners/browsers drain. Summary
`.scratch/web-read-fixture-spvnt888/SUMMARY.json` SHA256
`09931e5ba1d6c9a87625bfb05e70fe7a07b4ba6141fe6da1f5e0cfbfbca51ccd`.
Source3 snapshot `71e7056b49adf28d59c81ac602233d009ac6425566dd93c0d84402dcbefec30d` is frozen for full gate3. Exactly four independent
test files differ from the installed runtime's source1; all other1384 regular
hashes/modes match. Proof: `source3-test-only-artifact-reuse-proof.json` in the
evidence directory. No completion is claimed until gate3 exits0.

Final bookkeeping checks pass78 plan/docs tests in8.76s, human211/helpers27 and
whitespace. Precommit preservation proof verifies all1388 source hashes/modes
still equal gate3; only the five declared bookkeeping files changed afterward.
Independent source/functional reviews found no remaining CARD07–09 gap.
