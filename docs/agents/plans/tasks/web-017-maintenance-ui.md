# WEB-017: Implement guarded maintenance and integrity remediation

| Field | Value |
| --- | --- |
| Status | completed |
| Plan | [Web UI replacement](../2026-10-20-plan-web-ui.md) |
| Phase | P3 |
| Depends on | [WEB-016](web-016-operations-and-reports-ui.md) |
| Branch | `feat/web-ui` |
| Work-package commit | `WEB-017: implement guarded maintenance and exact repair` (this commit) |

## Read before implementation

Existing maintenance routes/services; retention/recovery/repair docs; exact publication findings; operation controller and fixture failure matrix.

Also read the relevant sections of [architecture](../support/web-ui/architecture.md), [API contracts](../support/web-ui/api-contracts.md), [testing strategy](../support/web-ui/testing-strategy.md), [acceptance matrix](../support/web-ui/acceptance-matrix.md), and [human documentation map](../support/web-ui/documentation-map.md). Load only affected living contracts and ADRs through their indexes. Refer to the [source review](../support/web-ui/source-review.md) for pinned baseline evidence; current git wins over it.

## Scope and implementation requirements

Build dedicated flows for prune, unmanaged purge, recovery, quarantine cleanup and repair from exact findings. Reuse existing preview/apply endpoints and typed scopes; review selected identities/reasons/retention effects and demand explicit confirmation. Server re-evaluates scope/authority under its existing locks. Keep current protected, configured repositories ineligible for purge, quarantine IDs explicit, and repair same-SHA replacement evidence intact.

Render preview refusals/partial outcomes and transaction diagnostics, never turn a preview handle or plan body into deletion authority. Removing config and applying prune/purge remain separate decisions. Explain one-round pruning and over-retention safety. On integrity or unknown recovery states stop and present evidence/runbook paths. No automatic repair/recover/prune/cleanup, arbitrary file selections or archive initialization control.

Connect resulting receipts/events/reports to shared original-operation controller, preserve uncertainty on disconnect and safe handoff of exact keys/IDs. UI confirmations are useful intent but never replace backend proof.

## Unit and component validation

Test maintenance request builders, eligibility checks, exact revision grammar, confirmation content, refusal states, warnings/partial/integrity priorities and no implicit mutation from read/preview.

## Integration validation

Execute real domain fixtures for each preview/apply, changed scope between steps, common-lock contention, protected current, managed purge denial, ambiguous journal preservation and repaired publication identity. Retain existing crash injection regressions.

## Functional validation

Through Caddy browser flows perform safe prune/purge/quarantine/repair/recovery on tiny owned fixtures, verify exact on-disk outcomes/audits and preserved unknown evidence, and lose an apply response without replay. No production/NAS data is involved.

## Human documentation deliverables

Create maintenance.md with prerequisites, effects, confirmations, safe stop conditions and links to existing recovery/operations contracts. Use only clearly labelled fixture examples; update relevant error help.

## Acceptance

Every existing maintenance capability is available with truthful previews and strict backend authority; destructive or ambiguous cases cannot bypass safeguards through the UI.

The task also requires the existing `scripts/check.sh` gate plus strict applicable web/Cockpit and functional checks described above. New capabilities are not completed solely by adding test descriptions. Update actual test-to-case mappings and run them. Documentation and relevant contract/invariant/ADR updates land with the behavior, not in a later catch-up task.

## Execution notes and blockers

Activated 2026-10-26 after WEB-016 committed as `b48bc53`. Reuse the nine
existing typed maintenance actions and shared original-operation controller.
Implement successful same-session preview review with explicit one-use
confirmation; the backend re-evaluates current scope and locks. Every raw edit,
connection change, navigation and first apply attempt retires confirmation.
Repair starts from a decoded exact verification finding and explicitly reads
fresh retained reference/manifest evidence. Existing repair is SHA-scoped, not
publication-ID CAS; show original, freshly observed and actual retired/new
publication identities separately.

Collaborating agents share this one package: maintenance state and unit tests;
root owns React workspace, component tests and integration; human guides and
contract review; and reuse of the established guest/Caddy/browser fixture with a
fresh .38 runtime. Preserve all prior .36/.34/.32 evidence and WEB015 pending
configuration. No new engine framework or production effects are authorized.

Review covers retention/repair and transaction/recovery invariants AD04–06,
AD13/16/20, FS14/18/19/20, TX01–07 and shared browser INV020/021; existing
ADR117/134/137/145 and exact-publication decisions apply. The known lifetime
generation/audit-union gap remains explicit. Record actual gate, domain and
installed browser evidence here before completion. No acceptance is claimed yet.

The first implementation adds a dedicated Maintenance workspace and exact
verification-finding handoff through the charged maintenance owner. Plan lists,
selected revisions, recovery diagnostics and quarantine proof render in bounded
25-row collections. Review caught and corrected an uncharged pending-navigation
finding alias and comparison of old repair results against a newer editable
finding; effect-specific captured proof owns result attribution. No endpoint or
runtime dependency changes are needed.

Focused real API/domain tests in `test_web_maintenance_worker.py` pass (2 tests,
5.54s): sequential model/dataset repairs preserve the first open grace journal,
original manifests and damaged predecessors while a real Unix worker verifies
replacements; lost genuine prune admission recovers via the original key with one
POST, one audit and one 5-to-4 round while preserving current. These supplement
existing maintenance scope, contention, crash and ambiguity tests. Required full
gates and installed Caddy/browser acceptance remain unperformed for this package.
The human maintenance guide and synchronized navigation/runbooks pass 216 human
and 27 helper documentation checks plus 69 focused documentation tests.

Full frontend precheck 1 passes 3,855 combined tests in 78.863s with no skips,
95.70% line and 89.82% branch coverage (required minima 90% / 85%). This includes
40 maintenance-state tests and exact finding/confirmation/navigation/result
association component regressions. Evidence is retained at
`/var/tmp/web-017-validation-n5qoqk8f/frontend-precheck1.result.json`, with the
immutable per-run report/coverage in `web/.artifacts/component-rvnAfB/`.
This precheck precedes the final strict source gate and is not installed browser
acceptance. Early fixture origin/receipt chronology and an incoherent blocked
recovery test input were corrected without relaxing runtime validation.



## Validation history

The following entries retain the chronological attempts and their original
results. Current completion evidence is at the end of this task.

### Frozen source and strict validation in progress

Source 1 is frozen at
`b740b530690bafcc730e590c448257a9a8648de8cce92092a50944d87818f393`,
1,481 regular inputs, with only task017, dated plan, current selector, acceptance
ledger and progress excluded as bookkeeping. Strict gate 1 is running against
that same identity; no pass is claimed until its result exists. All owned source,
unit/component tests and human contracts remain frozen during artifact and
installed acceptance work.

The first local artifact wrapper stopped before creating any artifact directory
because it used host Python 3.12 against the project's Python 3.14 syntax
(exit 1, 0.175s). The original log/result remain retained. Build attempt 2 uses the
locked `.venv/bin/python -I -B` interpreter and the same unchanged frozen source;
there is no application or gate exception.


Matching artifact build attempt 2 passes (exit 0, 64.713s). The shared image
`12b5d456b9d22c34fa3b32c20825b27962189bc6c466c8451dc6031e96cd67a6`
contains UI manifest
`4a0b1618980636c6ade93f090292c7d9dd1ad84f1fec961c452404b3d5e39f08`.
Actual pinned UBI 10 micro foundation and network-none/read-only UID981 probe
pass, with no Node, package managers, uv or pip. The first private probe used the
architecture example asset path instead of the recipe's actual `/opt/hfcache/ui`;
its exited-1 container/log remain retained, and corrected probe 2 passes without
an image or source change. Probe 2 SHA256:
`a7daf88c1183afe75e097eb96da2f448d155e5ee7f8805784fa0f7b78a70366a`.
Current artifact summary: `E/source1-artifact-summary.json`, where
`E=/var/tmp/web-017-validation-n5qoqk8f`.

Owned native .38 staging passes exit 0 in 9.298s, with all 114 installed Python
modules byte-identical to the frozen wheel/source and matching UI. The existing
.36 selector and 1,150 preserved old WEB015/.32/.34/.36 objects remain exact.
No services or browser cases start at staging; fresh fixture setup is separate.


Fresh fixture preparation also passes all six finite stages (setup, draft,
install, profile, labels and additive Caddy mask 73), preserving all 1,150 old
objects. The .38 archive UUID is `376f2bda-9b3b-40ab-84a2-75f1b5c0448b`.
`E/source1-fixture-all-results.json` retains actual commands and elapsed results;
no services or browser cases start during preparation. Fixture seeding and the
39-case installed browser matrix remain separate acceptance work.

The built initial JavaScript measures 188,858 gzip bytes against the 358,400-byte
engineering target, with Markdown in a separate chunk. This static size check
(`E/source1-bundle-size.json`) is not a latency or Caddy-compression claim.


### Current strict pass and retained installed-fixture failure

Strict gate 1 passes exit 0 in 1,647.475s on source 1 / 1,481 inputs with no
source drift: 8,610 backend tests, 3,597 web unit and 3,855 combined frontend tests,
zero required skips, final 95.00% line / 90.10% branch coverage and all required
Cockpit, type, lint, documentation, build, wheel-profile and read-fixture checks.
Result SHA256:
`8e94c7e6e062d48bc38474a98498d97fab99988324ee38ef4b4cbeb3286a95f1`.
MAINT01–06 record actual unit/integration evidence but remain in progress.

Original installed cohort `c42b99d58f6c41028164533c23b68b70` passes its first eight
Chromium workflows, then fails the lost-prune case. The original prune operation
`67ded8626e2208c32af1a49ae49aa42a` actually fails 50/HFRET002: synthetic Hub cache
symlinks name the physical fixture root, outside the service's writable virtual
archive bind. The fixture must use cache-local relative symlinks as the real Hub
cache does; no application or confinement relaxation is selected.

The original collector stays false/cleanup-unknown. Its normal controller drain
records 13 stopped pairs, four empty cgroups and five refused endpoints, but a
separate caller comparison wrongly treats four newly created legitimate journals
as changes to originally held files. Read-only retrospective closure will be
recorded separately; it cannot promote the failed cohort. Preserve all nine
receipts and its partial archive/journals without replay or cleanup.

A fresh .40 / web017b application fixture is being built from the same unchanged
source 1, with only isolated artifact-version metadata projected. Existing guest,
Caddy and browser engine are reused. Correct only the synthetic cache adapter and
its caller's original-path subset/new-journal checks. The complete 39-case matrix
must still pass on the fresh archive before this package can complete.


C1 read-only retrospective closure v2 passes exit 0 in 1.360s, separately from
acceptance. Proof SHA256:
`b9623b8463eaabd3988a9d26e4b9102faef3f09b9be107b5595758ff8cbe0729`.
All 27 collected original files retain full identity/SID/digest, 13 controller
pairs and two callers are gone, cgroups/endpoints close, baseline five and all
1,150 old objects remain exact. The failed prune journal remains open at
`plan_persisted`, with five revisions/current preserved. Original result SHA
`af0ddf51c4dc81cae82463c36fac9ffab98de41f721d03912263ebaa7805c7c8`
and its false/unknown flags are unchanged. The first closure collector's
list/tuple comparison failure is retained; v2 only fixes the private comparison's
JSON representation. No lifecycle/API request or guest write occurs in closure.

The fresh .40 artifact build passes in 53.941s on the same frozen source.
Image `4505c47d5b4ddf61e3e9da2916c3310cc4f65596fa9403b64b56a352c7e60615`
and UI manifest
`08f60fb2cd99587830477daae1c7ab422fffcca56b92ccbc8eca4bbc80e3f21d`
have actual pinned UBI 10 micro foundation and matching no-Node probe evidence.
Probe SHA256:
`e78bfd02040f2b0bb73eb311936240e2443ef7a9db1a166e5d7cd9ec7b079963`.
`E/source1b-artifact-summary.json` binds all artifacts. Fresh B fixture setup is
authorized only after known C1 closure; no acceptance is inferred from rebuilding.
A latent private lost-response assertion is also corrected from nonexistent
`record.operationId` to the actual `record.receiptIdentity.operation_id`; the
original C1 failure occurred before that assertion. Lookup and no-replay checks
remain required.


### Fresh B first-phase installed pass

Fresh .40 cohort `6a517c3346974e4898e7b86accc9ebdd` passes all 27 first-phase cases
in 271.793s, nine each in Chromium 156.0.8078.4, Firefox 157.0 and WebKit 27.2.
All 27 original POSTs are unique: 24 succeed and three correctly refuse configured
but disabled purge scope (10/HFARG007). Recovery, quarantine proof/cleanup, unmanaged
purge, protected-current one-round prune and genuine lost-header/reload/original-key
GET recovery pass without replay. All 12 new journals join the actual original
operations and explicit fixture sources. There are 205 trusted browser requests
and 54 empty CSP checkpoints. Normal cleanup proves 13 process pairs gone, four
empty cgroups, five refused endpoints and unchanged held inputs/all 1,837 old
objects. This phase does not exercise history paging or establish rootless/NAS
acceptance.

Current evidence under `E/functional-phase1b-1-observed/`:
root result SHA256
`dfcb1a0f82dc721dcbbf9739b4afeb1f18e64ce0aed2222ec4d051712e6396fc`;
browser report
`5b553511fe6970d964cd880a9dc3dd9c25af012f25f809392f223e26e15576e8`;
86-file extended original-metadata manifest
`c66e05e862061917362ebde0f97efcf9228f4fc63eb54b832ad106325331d846`;
derived receipt/result summary
`340cb87b128a192dc806be6dd9410b865da6654709bf24fe0d3153b2acbb2ff9`.
The repair and final ambiguity phases remain required; no task completion is
claimed. Existing reviewed phase runners have conditional authorization to proceed
only after each actual success/effect/normal-drain proof, stopping on unexpected
or unknown outcomes without retries.


### S2 application fix after the installed repair-read failure

Original .40 repair cohort `4b5080a1fb9c4f8686b6ba48423e6c05` fails exit 1 in
60.696s, before any UI repair POST. Its genuine full-verification prelude
`fa3004ae327ff80147f981423ff1cffe` / run `9391f9c71e2a4017b568914d7ade842c`
returns 40 with three findings and identical API/worker result bytes at SHA256
`7925dc94cc6cc0cc42110b4edc458000412b8cd5a757b10b9ca0ee1a6b273720`.
Normal cleanup passes: 13 pairs gone, four empty cgroups, five refused endpoints,
all old/held evidence unchanged. Original result SHA256
`dda3c8f1206fc33b78ba53a57b2c3083a38a2a8b09255897df0fb041a595de5c`
remains false. No ambiguity setup or retry occurs.

A controlled unchanged-source integrated diagnostic reproduces the actual trace:
a ready RepositoryStore manifest remains subscribed after route pause;
Maintenance's distinct reference GET succeeds, then its identical manifest query
is locally refused as a duplicate active owner. Releasing the old repository
owner makes the same ref–manifest–ref proof ready with zero POSTs. Diagnostic
`E/repository-maintenance-duplicate-diagnostic-result.json` SHA256
`9f7a38b8f4e4c10d0297b793440f794283cb6212d121936a1fc034f2e30ae75d`.
Original DOM/status bodies were not captured; that absence is recorded, not
reconstructed as historical evidence.

S1 is explicitly unfrozen for this necessary application correction. S2 uses
existing repository retire/forget semantics on route pause, releasing all read
subscriptions and aggregate payload aliases while retaining target/tab/exact
bookmark IDs. Reopening performs fresh scoped reads and retained-SHA membership
checks. Query identity, duplicate-owner refusal, byte limits and operation state
are unchanged. New state and full loaded Repository→Activity→Operations→Finding→
Maintenance regressions cover the real composition. All 71 focused checks, whole
TypeScript, lint and format pass; the four affected contracts/guides pass 69 docs
checks and 216 human/27 helper alignment. A new strict S2 gate, matching .42
artifacts and a fresh complete 39-case environment are required before completion.
All .38/.40 archives, damage, pending journals, receipts and failed evidence remain.


S2 is now frozen at
`8e320cf16ced0020feadc21c6d8492ba50383abc244b3c83fca3a57b52707691`, 1,481 inputs.
Only the seven stated source/test/contract files changed from S1. Strict gate 2
and matching .42 wheel/UI/shared micro image build are running; earlier S1 passes
remain historical. Fresh C fixture preparation will preserve the entire failed B
archive, three damaged publications, original verification and browser evidence.
The complete 39-case matrix must pass on S2 before committing.

### Current S2 installed acceptance

Matching .42 artifacts pass build in 66.024s. Shared image
`39037aaff2ccf4fc8f7398efba617b62b1e4d191a7e69181a6fb061befe8311a`
and UI manifest
`508d97a7397195e37ecd5612c715f81b82c9fbc81325e409a93502c75b9dcf50`
match S2, with actual pinned UBI 10 micro and no-runtime-Node proof
`0f9673094d69e8f2a2cf20ffd6aa9e1117d1e8d3d89562a9e47293426bb53ec6`.
Fresh C preparation preserves 4,128 older objects, including B's failed repair
evidence and damaged publications. Its archive UUID is
`66cebdbf-a04b-4a55-bf19-010de9a2eb51`.

C phase1 cohort `0cfe443b1ff74596b2c675ec9de591f6` passes all 27 cases in
367.048s, nine per Chromium/Firefox/WebKit. The 27 unique original POSTs and 12
journal joins prove recovery, explicit quarantine cleanup, disabled configured
purge refusal, unmanaged purge, protected-current pruning and lost-header/reload
original-key recovery without replay. All roles close normally: 13 pairs gone,
four empty cgroups, five refused endpoints and all older/held evidence unchanged.
There are 225 trusted browser requests and no CSP violations. Exact 87-file
manifest SHA256:
`d4ac463aed932156e76465dd052e63727b69b976cc16ca31f422b21fee220798`;
root result:
`a1374a9e71cb45a8384913dd5b7c06d1c98832a4e8ec89b2fa9986e637b69cf7`;
summary:
`024c0db9d21dc2a7e3a95b5666fd40782e5457740ea74a28f245082255d6a680`.
Evidence is under `E/functional-phase1c-1-observed/`.

Repair preparation ran once only after that success and known closure. Current
repair cohort `cb3ba90eb5ff41c996e742ee5c14827e` is running its nine browser cases
after one genuine full-verification prelude. The strict S2 gate and all remaining
repair/ambiguous-recovery cases must pass before completion. This remains
LOCAL_STORAGE_SIMULATION, not NAS or new rootless/platform acceptance.

The repair browser completes all nine cases and three unique original repair
POSTs, but the final private preservation collector raises `AssertionError`.
Original host result remains exit 1 (119.123s), with `passed=false` and
`cleanup_unknown=true`; it is not promoted. The controller itself records normal
closure (13 pairs gone, four empty cgroups, five refused endpoints, fixed input
hashes unchanged). The failed comparison precedes the held/effect proof fields.
Read-only diagnosis will identify that exact mismatch and verify original disk
effects separately. Final ambiguity preparation and execution have not started.

Read-only comparison identifies exactly three differences among 188 held paths:
the retired README files keep the same bytes, device/inode, owner, mode, size,
mtime and SELinux identity, while link counts drop from two to one and ctime
advances. Original repair removes the implicated canonical cache revision through
the provider, legitimately releasing those hardlink aliases. All other 185 held
paths, including damaged predecessor configuration files, retain full recorded
identity and bytes. All 4,128 older objects and five baseline pairs remain exact.
The full-identity assertion was stronger than this valid cache-release behavior;
the original false/unknown collector record remains unchanged. Separate finite
read-only closure must join those precise changes to the original repair windows,+journals, receipts and grace records before final recovery can proceed. No job is
rerun to manufacture a passing collector result.

Independent read-only repair closure passes exit 0 in 13.841s, SHA256
`a431a84efe1bbc08a6453fc27ec09e7137568aef41b29a485482a4422c08cc98`.
Each of the three exact link/ctime deltas lies within its original repair and
cache-deletion checkpoint interval. All receipts/results, three 168-hour grace
records and open `repair_committed` journals join the actual repairs; the genuine
full-verification prelude's API and worker bytes agree. Original roles are gone,
cgroups empty and endpoints refused. Read brackets remain unchanged; this proof
performs zero API/lifecycle calls or guest writes. Historical fixed-input full
metadata was not persisted, so only the original controller's input-hash proof
is claimed for those inputs. Root qualification
`758975abb90ee7ac1891668a7b81dc2fc5f1f1f2cc297a3353a203d0fe882d75`
accepts the actual nine browser/effect cases with this separate closure; it does
not change or promote the original false/unknown collector result. The existing
final three ambiguous-recovery cases are authorized once, without later healing
or jobs. Strict gate and their actual pass remain required.

S2 strict gate 2 now passes exit 0 in 1768.399s, with all 1,481 source hashes and
modes unchanged. Command: `rtk proxy scripts/check.sh --require-web
--require-cockpit`. Actual results: 8,610 backend tests (52 unrelated opt-in
deselections), 3,599 frontend unit tests, 3,858 combined unit/component tests,
95.06% line and 90.29% branch coverage, 581 Cockpit unit tests and 110 mounted
checks. All required lock, format, lint, types, generated-wire, documentation
(216 human documents / 27 helpers), wheel profiles, production builds, browser
startup and real API read-fixture checks pass, with no required skips.
Result SHA256:
`7f2282e4c804e1f236d8fe7005201fbc4b5984f9032ae6805a5fddf4162c4a4b`;
log SHA256:
`c92ab15ae1bdd9c6bb131082fe90eba307b8f9fe1b0628cecf8bb438751bd2ee`.
The final three ambiguity cases remain running; completion is not inferred from
this successful source gate.


## Completion evidence (2026-10-27)

WEB-017, this commit, completes guarded maintenance and finding-based exact-SHA
repair. The existing typed endpoints and original-operation controller remain
the execution boundary. Previews and one-use confirmations grant no backend
authority; edited input, navigation, authentication and first Apply retire them.
Repair compares original finding, fresh publication proof and actual old/new IDs
without inventing publication-ID compare-and-swap. The repository route releases
read subscriptions and aggregate payload references on pause, retaining exact
bookmark identity and requiring fresh membership on return.

**Current source gate.** `rtk proxy scripts/check.sh --require-web
--require-cockpit` passes exit 0 in 1768.399s on S2
`8e320cf16ced0020feadc21c6d8492ba50383abc244b3c83fca3a57b52707691`,
1,481 regular inputs with zero hash/mode drift. All 8,610 backend tests, 3,599
frontend unit tests, 3,858 combined frontend tests, 581 Cockpit unit tests and
110 mounted checks pass. The 52 deselections are unrelated opt-in tests; there
are no required skips. Coverage is 95.06% lines, 90.29% branches, 93.32%
statements and 94.92% functions. Lock, format, lint, types, generated contracts,
216 human-document/27 helper alignment, all wheel profiles, production builds,
sandboxed startup smoke and real API read-fixture checks pass. Gate result/log
hashes are recorded above; `E/gate2/summary.json` independently joins all 39
mapped frontend node names to the current machine reports.

**Matching artifacts.** Owned .42 wheel/UI/shared image build passes in 66.024s;
only fixture artifact version metadata differs from canonical project 0.2.2.
Image `39037aaff2ccf4fc8f7398efba617b62b1e4d191a7e69181a6fb061befe8311a`
and UI manifest
`508d97a7397195e37ecd5612c715f81b82c9fbc81325e409a93502c75b9dcf50`
match S2. Actual pinned UBI 10 micro ancestry and the read-only/network-none UID981
probe prove no runtime Node or package managers. Exact wheel, source and UI tar
hashes are in `E/source2-artifact-summary.json`.

**Installed functional acceptance.** All 39 one-attempt browser cases pass through
the production-built UI, same existing trusted-TLS Caddy, installed Basic API,
helper and genuine private Unix worker. The reused owned native fixture has
archive UUID `66cebdbf-a04b-4a55-bf19-010de9a2eb51`. Chromium 156.0.8078.4,
Firefox 157.0 and WebKit 27.2 exercise 27 main maintenance cases, nine repair
cases and three final ambiguous-recovery refusals. There are 33 unique original
browser POSTs plus one genuine full-verification prelude, 331 trusted browser
requests and 78 zero-CSP checkpoints. Real receipt/result, journal, audit,
protected-current, same-SHA/generation, original-key loss/reload recovery and
168-hour grace evidence are checked without replay. This does not exercise
history paging or a new daemon restart; the corresponding existing unit and
integration mappings retain their narrower claims.

The repair coordinator remains exit 1 / false / cleanup-unknown because its
full-nine-field assertion rejected three legitimate provider-cache hardlink
releases. Its nine actual browser cases and three successful original effects
are qualified by the separately pinned read-only closure and root decision
above, not by changing its flags or rerunning repairs. Of 188 held originals,
185 retain full identity; the three retired README files retain bytes, inode,
owner, mode, size, mtime and SELinux identity, with only link count and ctime
changes inside the original cache-GC checkpoint intervals. Damaged predecessors
and original manifest expectations remain exact. Historical fixed-input full
metadata was not persisted; only the original controller's input hashes are
claimed there. Earlier C1/B failures and successful S1/B partial evidence remain
chronological and separate.

Final ambiguity cohort `b691bd5741fc40b0bd2484ef65a8506e` passes in 78.178s,
with three exit-20/HFTXN004 original previews, no Apply and zero new journals.
All 549 archive objects, 65 prior journals, three grace records and ambiguous
journal `97c38426a5ce4b82a23c8f0124a1a96a` remain unchanged. Original 13 process
pairs are gone, four cgroups empty, five endpoints refused, five baseline pairs
and all 4,128 older objects exact. No later job, healing or cleanup occurs.
Final root result SHA256:
`12fe3d49f5046f0327cee58935d2f3185ee9f0bc05f376d5e6b9fbd516c6226c`.
Current aggregate `E/source2c-functional-all-summary.json` SHA256:
`e3aeaf48711d8c93488898bbef5b17984b351b739947b05c5908eccbb4c768cf`.
This is LOCAL_STORAGE_SIMULATION application evidence, not live NAS, production,
new rootless UI or WEB022 platform acceptance.

**Contracts and human guidance.** The maintenance guide, navigation, operations,
recovery and troubleshooting explain exact scope, explicit review, safe refusal,
finding evidence and no-replay observation. Focused documentation checks pass
69 tests; strict alignment checks cover 216 human documents and 27 helpers.
Review covers AD04–06/13/16/20, FS14/18–20, TX01–07, INV020/021 and
ADR117/134/137/145; ADR117/145 and INV021 are amended. No endpoint, dependency,
privilege, durable format or architectural decision is added. MAINT01–06 retain
exact current unit/integration/functional mappings and failed historical records.

[Progress and handoff](../../progress.md#operator-handoff) record completion;
[WEB-018](web-018-schedule-observer-and-journal.md) is pending through the
[current selector](../current.md). Evidence root: `E=/var/tmp/web-017-validation-n5qoqk8f`.
No production, NAS, live Cockpit, rollout, merge, push or Git tag action occurred.

After recording completion, documentation alignment passes again (216 human
documents / 27 helpers, 7.222s), and all 78 affected plan/evidence/documentation
tests pass (16.339s wrapper; 15.03s pytest). The final source comparison still
matches all 1,481 strict-gate hashes/modes exactly. `git diff --check` passes.
Records: `E/final-bookkeeping-{docs,tests}.result.json` and
`E/final-bookkeeping-source-comparison.json`. The ledger preserves 23 historical
executions and appends 22 current executions, keeping the original failed repair
collector separate from its qualified evidence.
