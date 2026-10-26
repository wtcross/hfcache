# WEB-011: Build authority-scoped query state and durable browser observation

| Field | Value |
| --- | --- |
| Status | completed |
| Plan | [Web UI replacement](../2026-10-20-plan-web-ui.md) |
| Phase | P3 |
| Depends on | [WEB-010](web-010-repository-card-read-api.md) |
| Branch | `feat/web-ui` |
| Work-package commit | `WEB-011: preserve original operation recovery across browser sessions` |

## Read before implementation

Typed client; Cockpit operation registry/recovery/event/failure tests; operation endpoints and errors; architecture operation constraints.

Also read the relevant sections of [architecture](../support/web-ui/architecture.md), [API contracts](../support/web-ui/api-contracts.md), [testing strategy](../support/web-ui/testing-strategy.md), [acceptance matrix](../support/web-ui/acceptance-matrix.md), and [human documentation map](../support/web-ui/documentation-map.md). Load only affected living contracts and ADRs through their indexes. Refer to the [source review](../support/web-ui/source-review.md) for pinned baseline evidence; current git wins over it.

## Scope and implementation requirements

Implement the route-independent operation controller and bounded session recovery registry. Generate/store original key before POST; validate same authority/archive/subject scope; block submission on unresolved operations or pre-submit storage failure; preserve in-memory handle and block after post-submit storage failure. Restored terminal summaries require authenticated original observation before unblocking. Keep 32-record/64-KiB bounds and never evict unresolved entries.

Separate query loading/stale/unavailable/failed from operation queued/waiting/running/terminal/interrupted/observation-unknown states. Preserve request versus domain IDs and raw classified structured results through decoders; never parse human messages for authority. Poll result/events with finite read retry/backoff and cursor sequences, show gaps, stop when appropriate and keep observation after route changes. Abort read observation, not the backend operation. No POST retry/cancel/recover after timeout.

Clear private caches on changed authority/auth failure without discarding unresolved safe handles; prevent restored cross-origin/archive entries from auto-observation or auto-rebinding. Cross-tab coordination is bounded and advisory; backend idempotency/locks remain final. Provide manual original-key/ID lookup for migration from Cockpit.

## Unit and component validation

Test full registry/state transition matrix, corrupted storage, quota pre/post POST, restored metadata, scope drift, limits, event gaps, 202 semantics, no automatic retry and failed Envelope classifications.

## Integration validation

Use real operation API/runner/store with lost admissions/results, restart, expired/missing history and original-key lookups. Assert exactly one actual effect/operation even across remounts and observer timeouts.

## Functional validation

Through browser/Caddy start a fixture operation, navigate/unmount/reload, disconnect/reconnect, reopen original handles and preserve unknown state. Run two tabs and storage failure injections; inspect that no secret/TOML/body is persisted.

## Human documentation deliverables

Create user operations/reconnect guide and troubleshooting decision paths, including original handles, browser-session limits, stop-observing versus cancellation and missing-history stop conditions.

## Acceptance

Operation observation survives the supported UI lifecycle without replay and without false outcomes; all uncertainty/limits are visible; original safe handles remain recoverable and authority-scoped.

The task also requires the existing `scripts/check.sh` gate plus strict applicable web/Cockpit and functional checks described above. New capabilities are not completed solely by adding test descriptions. Update actual test-to-case mappings and run them. Documentation and relevant contract/invariant/ADR updates land with the behavior, not in a later catch-up task.

## Execution notes and blockers

Started2026-10-26 after WEB-010 `beebb7a` and a clean checkout. Implement the
accepted application-owned registry/observation design with existing typed client,
React and APIs. Root owns shared contracts, session controller/mount/recovery UI,
acceptance and commit; registry, query/event state and human documentation are
collaborative scopes within this package. Query/session identity includes local
auth generation as well as server scope; original operation authority remains
historical. Restore Basic-key handles through authenticated original-key lookup
before trusting saved IDs. Legacy Cockpit keys do not share Basic namespaces;
manual ID observation never proves key ownership or resolves another record.
No POST replay/cancel/cleanup or secret/body persistence. Preserve LGPL provenance
and artifact notice for ported registry code. Shared encoded retention budget and
finite read sessions must remain visible on refusal. Reuse owned application
fixtures; no production/NAS/live Cockpit/rollout/publication actions.

## Completion evidence

2026-10-26, WEB-011, this commit. Commands: scripts/check.sh --require-web --require-cockpit (gate2, exit0); the owned guest launcher with web-011-run-native-source2.py and functional-descriptor-source2-v1.json (exit0); source2 stock build plus check-container-foundation.py (exit0). No required acceptance check is skipped.


- Implemented the route-independent original-operation controller, bounded
  authority-scoped query/evidence state, event observation, durable safe-handle
  registry, explicit reconnect and built recovery interface. Original keys persist
  before transmission; uncertain admissions never replay. Restored summaries
  remain unverified; imported IDs establish no creator/key association. Legacy
  bearer references remain separate from Basic-subject namespaces.
- Recovery metadata is32records/64KiB with unresolved growth reservation;
  retained encoded evidence32MiB, each session read8MiB clamped to its route,
  two concurrent reads globally/one per handle, initial GET plus at most three
  eligible retries at1/2/4seconds,120cycles/five minutes, and32events/64KiB per
  handle. Query handles survive route remount only within one AuthSession;
  reconnect permanently retires old handles. Cross-tab notices are bounded
  advisory signals without automatic merge, settlement or execution authority.
- Local LGPL registry provenance/full license is retained in generated notices;
  no Cockpit bridge/runtime or new npm dependency is introduced. Full job forms,
  the complete Operations workspace and subsequent domain views remain future work.

### Source and strict gates

- Historical gate1 **PASS1577.982s**,8581backend tests,3130required web unit and
  3211required component-suite tests as reported by that gate, plus strict
  Cockpit/web/build/browser/read-fixture checks; no required skips. Source1412
  snapshot `9e56c017fc327800e70f0738197bbdcccf838c857f418d23810d0a668a9ed75b`.
  Evidence: `/var/tmp/web-011-validation-1oxmmhrk/gate1/{strict-gate.log,strict-gate-result.json}`.
- Gate2 **PASS1501.198s**:8581backend/52unrelated opt-in deselections,581Cockpit unit/110mountedFirefox,3131web unit/3214combined component; statements94.23%, branches91.71%, functions92.98%, lines95.46%. All strict types/lint/generated contracts, wheel installs/build, two startup Chromium and14real API browser checks pass with zero required skips. Final log SHA b740b922e333252a04295d4341290a63b970e20af3f1c058ef74fab667a3e32b.
  Frozen final source1413 snapshot
  `d1edf7be6cc65379808839bfa5d09ddb4eb7ce280d5c58f613c02f71d78f2e25`.
  Evidence: `/var/tmp/web-011-validation-1oxmmhrk/gate2/`.
  Gate1 does not qualify the later fetch-receiver correction by itself.
- Source2 artifact/source comparison verifies all1413 gate files with only the
  two declared fixture version projections (`pyproject.toml`, editable self entry
  in `uv.lock`). Proof `source2-artifact-gate-proof.json`, SHA
  `36261c7db4daabdb52ca2296d35a4a61a46b5d9a61e2788202df7d1f74ab83f3`,
  under the validation directory. Fixture native version0.2.18 is not a canonical
  version bump or a production deployment.

### Installed functional evidence

- **PASS89.587s**, generation `9c370a5c17dc4683a8491409a2226c31`, one real
  sandboxed Chromium against the built interface, shared trusted-TLS Caddy,
  installed indexed native API and genuine protected helper. Actual owned
  read-only loopback NFS is used; there is no mount-table/statfs/business-response
  substitution, live NAS claim or new full platform-matrix claim.
- All nine cases pass once: lost202/original-key lookup; route remount and
  unverified reload; actual API restart and explicit reconnect; pre-send storage
  quota/zero transmission; offline-before-send followed by genuine missing lookup;
  post-admission quota retaining the in-memory ID/block; two-tab advice without
  automatic merge/submission; missing manual ID/unknown creator; corrupt storage
  retained with submission blocked. Local storage/transport fault injection is
  an explicit unshipped browser-controller seam; real authentication, admission,
  operation store, runner and results remain unchanged.
- All47requests are captured within the unchanged256 limit:45GET/2POST, exact
  trusted origin, no invalid/overflow observation. Exactly two original Basic
  installed Plan admissions exist, both succeeded with `repositories:[]`.
  They demonstrate admission/observation and no replay, **not archive write effects**:
  `a54c8936f8de11f08d7017b55b92232f` →run `5c4c9a68f8164650984a5a1af21c335f`;
  `49acfcc2271419a7ce395ea7fdbc80e2` →run `cdfc380cc30947718a2d1b850b0af9ff`.
- Original API167680/start6798184 is normally stopped and gone before new
  API168027/start6802059; instance changes
  `54a969ba4730451a93af01e01c692037` →`2c27ee234ba244fe8768576e92132c88`.
  Helper and Caddy retain their original cohorts. All application roles, tracked
  children, cgroups, endpoints and browser descendants normally drain;
  `cleanup_unknown=false`, five original baseline pairs unchanged. Configuration,
  original lock/key and read-only archive metadata remain unchanged.
- Complete host evidence:
  `/var/tmp/web-011-validation-1oxmmhrk/functional-native-source2-evidence.json`,
  SHA `d20139ef2ee1f30d40bb785fae1a350bba6848d955c52ae1b88ce24fd9da6029`.
  Root result SHA `45382a9fbe06dae4eb8f3491c89e8ea8e4076697f4be9ec064446e776ccb13c4`;
  browser report SHA `2d358f74de4b53a5254bb48a68e1e49cad4473bb0af57582a665ad5b5d8c6871`.

### Integration and regression mapping

- Actual write/no-replay integration is separate from the two empty Plans:
  `tests/unit/test_api_command_adversarial.py::test_lost_http_acknowledgement_does_not_cancel_real_sync`
  uses real ASGI/runner/store, a lost202, one owned toy publication and one
  external HubFake download; same-key duplicate returns the original ID.
  `tests/unit/test_api_catalog_refresh.py::test_lost_http_acknowledgement_keeps_one_owned_refresh_and_key_lookup`
  calls the real CatalogWriter once and writes one real `repository_tag_snapshot`.
- Real framed Unix/configuration-writer restart coverage:
  `tests/unit/test_configuration_application_integration.py::test_api_unix_writer_exact_install_and_original_recovery[disconnect]`
  and `[result-persistence]` retain exact predecessor/lock and one `config-apply`
  call through API restart. Their external authority/SID capture adapter does not
  constitute MAC or NAS acceptance.
- Missing/expiry/interruption remain uncertainty:
  `tests/unit/test_api_operations.py::test_missing_lookup_is_uncertainty_not_proven_nonexecution`;
  `tests/unit/test_operation_store_adversarial.py::test_expired_terminal_with_unavailable_result_is_preserved[missing|changed|symlink]`;
  `tests/unit/test_api_catalog_refresh.py::test_restart_preserves_abandoned_refresh_without_execution_or_replay`.
  These existing backend nodes are included in the8581-test gate selection.
- The actual native failure led to the central fix binding both supplied and
  default fetch to `globalThis`. Focused regression nodes are
  `web/test/api-client.unit.test.ts` — “an explicitly supplied branded fetch keeps
  its global receiver for GET and POST”; and
  `web/test/native-fetch.component.test.tsx` — production default mount host read,
  plus restored uncertain original-key receipt/result observation without POST.
  Query/registry/session/event/cross-tab and mounted recovery matrices cover the
  remaining bounded states; final complete counts belong to gate2 above.

### Retained failures and artifacts

- Source1 artifact build1 exhausted disk. Its original
  `/var/tmp/web-011-artifacts-source1-1oxmmhrk/dev-api-ui-context-41ohve81/build.log`
  remains; same-context `build2.log` and the stock foundation pass are distinct.
  Eight closed ignored build directories were relocated without deleting bytes,
  modes or links, with original paths retained as symlinks; exact proof:
  `/var/tmp/web-011-validation-1oxmmhrk/owned-artifact-relocation.json`.
- Original native functional1 **FAIL82.237s** is retained, never promoted:
  `functional-native1.log`, `functional-native1.result.json`,
  `functional1-actual-safe-state.json` in the validation directory; guest result
  `/opt/hfcache-web006/helper-web011/cohort-e7d0283839df4fc1bd0effede6cd7ee7/RESULT.json`.
  Actual Chromium rejected an unbound native fetch receiver. Its one backend Plan
  `3f12355d49aacf3c33bb60be32515e45` had succeeded; a failed browser did not prove
  nonexecution. Original key/receipt/result are retained without replay.
- Before the independent source2 cohort, the whole stopped source1 API store was
  preserved by same-filesystem NOREPLACE rename, retaining all original leaf
  full9/SIDs/hashes and allowing only directory renamectime. Proof SHA
  `3f8c3d44c5f9ebebc3c228224df4d50d9d8360b9481248f44cd2709064fe0d9a`,
  included in the host evidence; guest copy
  `/opt/hfcache-web006/helper-web011-source2/retained-source1-api-store.json`.
- Final stock record: `/var/tmp/web-011-artifacts-source2-1oxmmhrk/stock.json`,
  SHA `b97ad18f8ea54f29439e878fec17d48096b474e493f619522e298b7ef5e2d79e`.
  Wheel0.2.18 SHA `ec7bf57064d87e72a2817c21eca48b547a6fd98cb9e4eab46b8bf92b123571e1`;
  UI manifest `8821fa04f766a40f6a17cd82cef0ce333c670e277031af14fb47f6cd8ab13bfa`;
  pinned stock UBI10-micro image
  `sha256:a603f14bedddb753c4544f4104c64a55d6bae947807e2b74fdf37318ae531768`.
  Stock build/foundation pass is separate from native application acceptance;
  projected rootless0.2.19 is not a new rootless functional claim.

### Documentation and handoff

- New `docs/web-ui/operations.md`; human navigation/troubleshooting, API/client,
  security/schemas and development/license guidance updated. INV021 and explicit
  ADR134/137/145 amendments preserve original authority and no-replay semantics.
  Documentation alignment passes212human documents/27helpers.
- OPS01–05 now have executed unit/component, real runner/store integration and installed native functional mappings. The task/current/dated-plan/progress records advance to WEB-012. The final source-preservation check covers all1413 frozen inputs; only the five documented bookkeeping files change after the gate.
- The owned VM is drained and retained with source1 failure artifacts and source2
  evidence. No production/NAS/live Cockpit changes, rollout, merge, push or tag.

Final bookkeeping checks: documentation alignment passes212human documents and
27helpers;78plan/documentation tests pass8.56s. The precommit preservation proof
in /var/tmp/web-011-validation-1oxmmhrk/precommit-source-preservation.json confirms
all1413 frozen files and modes unchanged. Only the five declared bookkeeping
files changed after the full gate. OPS01–05 records name their actual executable
tests and evidence; no later acceptance case is marked complete by this package.
