# WEB-018: Preserve fixed schedule, observer and diagnostic host functions

Interface-only instructions and source references have been omitted from this
retained shared record. Exact original text remains in Git `c692d7ae4b866fefd8a743a21afdb729da0f39c4`;
original document path SHA-256 `eb263f122f2024ebe23d1f7b89f7ba4d0395c7f32197e438f2ad0d59b793a587`,
original content SHA-256 `5810adf2de1eb665ca6e9aafba326d415f01ab367b7a25cfb446acc0203ee3ec`.
Historical proof hashes identify the original artifacts, not this edited record.

| Field | Value |
| --- | --- |
| Status | completed |
| Plan | [Web UI replacement](../2026-10-20-plan-web-ui.md) |
| Phase | P4 |
| Depends on | [WEB-017](web-017-maintenance-ui.md) |
| Branch | `feat/web-ui` |
| Work-package commit | `WEB-018: implement guarded schedule, observer and journal actions` |

## Read before implementation

Also read the relevant sections of [architecture](../support/web-ui/architecture.md), [API contracts](../support/web-ui/api-contracts.md), [testing strategy](../support/web-ui/testing-strategy.md), [acceptance matrix](../support/web-ui/acceptance-matrix.md), and [human documentation map](../support/web-ui/documentation-map.md). Load only affected living contracts and ADRs through their indexes. Refer to the [source review](../support/web-ui/source-review.md) for pinned baseline evidence; current git wins over it.

## Scope and implementation requirements

Implement fixed sync schedule validation/change endpoints, observer stop, and bounded journal diagnostics through the narrow helper. Use actual systemd-analyze calendar/timespan with fixed argv, strict values, finite output/time and no shell interpretation. Managed drop-in apply/reset keeps ownership/mode, expected revision, backup/outcome evidence and explicit manager reload semantics. Pause/resume touches only the fixed sync timer and documented activation semantics.

Schedule and observer changes use keyed receipts and private durable helper outcomes with post-timeout read-only reconciliation. Stop observer requires the expected service/invocation binding and explicit supported-profile permission; it never claims cancellation of accepted API work. Never stop/start hfcache.target or API/worker, never enable verification timer, never redirect system names to user units. On the current rootless profile denied schedule/observer remains denied; test supported positive native behavior rather than create extra scope.

Journal GET exposes only a fixed source enum, finite lines/bytes/time and opaque bounded cursor, with redaction and explicit gaps. It is diagnostic, not an authority for operation completion. Wrong/missing helper policy, release drift, unsafe drop-ins, user-manager confusion or actual observer ambiguity refuses effects.

## Unit and component validation

Test action enums, calendars/timespans including shell/control characters, expected revision/invocation mismatches, managed drop-in paths, budgets/redaction, no target/verify timer actions and restart/unknown outcome classification.

## Integration validation

Exercise real helper sockets/files/processes in a guest and API operation reconciliation across timer/drop-in/observer actions; concurrently modify schedules and revoke policy to prove fresh refusal. Bounded journal stream cannot exhaust operation readers.

## Functional validation

Actual disposable systemd native profile: validate/apply/reset/pause/resume sync schedule and stop a proven fixture observer while backend work continues. Guarded rootless profile: same actions denied with real reasons, no service-manager fallback; verify timer stays disabled.

## Human documentation deliverables

Update administration/deployment/troubleshooting guides, host API effects, fixed manager and observer semantics, script inventory and schedule reference. Clearly label positive supported profile versus current guarded restriction.

## Acceptance

Historical execution summary: the recorded gate included the retired interface; exact invocation and original proof remain in Git `c692d7ae4b866fefd8a743a21afdb729da0f39c4`.

## Execution notes and blockers

Activated 2026-10-27 after WEB-017 committed as `bcde0dd`, with a clean working
tree and its strict source gate and all 39 required browser cases complete.
Reuse the established guest, existing Caddy and browser engine; preserve the
final ambiguous journal, repair grace and all earlier fixture evidence. No
production or NAS actions are authorized.

Implement the fixed host routes and independent durable outcomes through the
existing helper. Preserve HostStatus schema1 with a separate exact observer
status projection, original-key read-only outcome routes and existing rootless
schedule/observer denials. Native timer actions retain explicit pause/resume
activation semantics, revision checks, protected backups and manager outcome
certainty. Exact observer stop must target a retained original process identity,
not a show-then-StopUnit race against a replacement invocation.

Read-only preparation found that `requires_lock=False` still uses the domain
runner's single FIFO. A bounded fixed-route host-action lane must reuse the
operation store/runner lifecycle with disjoint route ownership so a scheduled
observer can stop while its accepted backend work continues. This requires a
recorded contract/ADR amendment before source changes; it does not add another
archive executor. Journal reads stay outside both effect lanes and are finite.
Full Administration forms remain WEB-019. No acceptance is claimed yet.

Decision156 and INV022 now record the fixed host lane, separate original-process
authority projection, pidfd-only stop, same-bind predecessor retention, versioned
outcomes and bounded diagnostic cursor. The API/helper/source ports are in
progress. Optional protected-label receipt v2 preserves the exact old v1 role
set for read/configuration profiles; native effects independently require the
four new fixed label roles and explicit grants. Existing HostStatus1 remains
closed; dedicated observer status represents the actual oneshot transient.

Initial focused checks pass: 19 real threaded runner tests (4.55s), including
archive flock held while a host action completes, disjoint startup and isolated
uncertainty; 22 ASGI/status/authorization checks (24.52s), including original-key
lost-reply observation without replay, fresh dispatch denial and durable known
stale refusal; and 109 existing private protocol/client regressions (1.96s).
Targeted API/protocol/runner/client/entry types report zero errors. Packaging's
172 focused checks and 69 documentation checks pass, with 217 human documents
and 27 helpers aligned. These are current unfrozen source checks; strict full
gate, matching artifacts and actual installed native/rootless acceptance remain
required. No guest service or archive action has occurred for this package.

## Verification history (original evidence retained)

Earlier verification checkpoint (2026-10-27; retained history): source freeze1 is
`a9f4de2d8006569892b4bf1bc0d1109daf730875fefb757769a36506fcbd22af`
over1498 regular files, excluding only this task, plan/current, progress and
the acceptance ledger. Matching native0.2.44 and rootless0.2.45 source/wheel/UI
and shared UBI10micro OCI builds pass; actual confined image probes verify the
installed UI manifest and absence of Node/package managers. Aggregate evidence:
`/var/tmp/web-018-validation-blcl67j1/source1-artifact-summary.json`
(SHA25632834c535e9f71495a28d9adaa3ac60d06c7e955c22b2cbc9a17851f4202e60e).
The canonical unshipped client/controller probe builds with zero source drift;
this is API-contract tooling, not completion of WEB-019 Administration forms.

Original strict gate1 fails after8861 backend passes/1failure/52 deselected
(1376.049s wrapper; zero source drift). The old narrow-reserve test chooses
floor(available GiB)-1, leaving1–2GiB headroom; at its16GiB reserve that does not
always fall below the application's10% warning threshold. The original sampled
statvfs value was not retained, so no specific concurrent disk change is claimed.
Its unchanged focused rerun passes once(3.225s) with1498 source hashes unchanged;
original config/report/log are retained. Full strict gate2 was later interrupted
as recorded below. The warning fixture is now deterministic while source is
unfrozen: controlled capacity facts preserve the actual sync/publication path
and all original warning/result assertions (1pass/2.47s; types/lint clean).
No product capacity behavior was changed.
The earlier frontend precheck's two independent stale inventory expectations
were corrected before freeze1; its original failed log remains retained.
Actual installed native/rootless acceptance is not yet established.

Owned native stage1 refused before staging because preserving all prior evidence
required78,030,779 bytes/6251 entries, exceeding its old64MiB aggregate collector
budget. The measured inventory is retained; only the ignored harness aggregate
budget changed to96MiB, keeping8192 entries,64MiB per-file bounds and all prior
paths. Stage2 passes(18.597s), with119 installed Python source files byte-equal,
the old selector and6464 original objects unchanged. Fresh synthetic namespace
setup, protected bootstrap publication and exact reviewed CIL installation pass;
historical global receipts remain unchanged. All native preparation phases pass.
Native functional1 starts and drains the installed roles but refuses before
browser execution because its private truth expected literal disabled/masked;
actual verify.timer is linked/inactive with no enablement links. Its original
false/cleanup-unknown result is preserved, with a separate read-only qualification
confirming21 original processes gone,4 cgroups empty,5 endpoints refused, all
prior objects exact and zero host outcomes. Functional2 refuses before service
start because that earlier API startup created the sole empty983:983/0600 store
`.lock`. Functional3 retains and checks that exact guard, uses separately measured
linked/unenabled timer truth and preserves both original failures. No timer links
or service policy were changed to satisfy either private harness correction.
WEB017C ambiguity and every prior handle remain intact. Installed acceptance
remains incomplete.

Installed conformance refinement: native functional3 fails the real verification
observer prelude with SDK HFAPI010 because its fixture allowed only Host127.0.0.1
while the stock Unix SDK sends localhost. Its original pending handle is retained;
all22 original processes drain and cleanup is known. A more important actual
native finding requires source changes: the default units do not explicitly
provision the assumed observer domain and the earlier stop path had no target
SID check. The native journal's init_t field describes the inherited stream,
not a sampled live process; the original SDK domain remains unproved.
Decision156 now requires an optional,
explicitly provisioned confined sync-observer domain, exact indexed context
fragment and pre-admission/original-process SID proof; no init_t signal grant or
unconfined fixture bypass is accepted. Schedule authority remains independent.
Root intentionally interrupts superseded gate2 gracefully (6159 passes/52
deselected, exit2,746.443s, zero source drift) before unfreezing source1. Its
cancellation request, original source/artifacts and all failed native attempts
remain retained. New source2, matching0.2.46/0.2.47 artifacts and a fresh full gate
will be required; none is claimed yet.

The confined-domain prototype now passes (attempt8,28.812s, cleanup known) with
direct live PID259566/start15853711 in `hfcache_sync_observer_t`, UID/GID983 and
empty effective/permitted/ambient capabilities. The actual indexed interpreter
is `bin_t`, delivered credential metadata is `init_var_run_t` (contents not read
by the probe), and authenticated Unix API listener SO_PEERSEC is the existing
`unconfined_service_t`. The candidate grants only needed directory/credential
reads and Unix connect, with writes confined to SDK state and no extra signal
target/capability/IP. The real original SDK operation
`069eaf2c15405e4026a151b0c148e3e3` waits on an actual held archive flock; normal
fixture observer shutdown preserves its pending file and the backend then
completes run `ceb0f1c9a09f456ea726c7687b561061`. This is an unfrozen .44 SDK/
API/worker prototype, not new helper-stop, Caddy/browser or source2 acceptance.
All failed prototypes and original SDK state remain retained. The one erroneous
owned hyphenated CIL module was extracted with its original checksum before
removal; the documented underscore module now contains candidate
`1a30d08b30e87fc1ffa910158977ac4021187131463c7cfdd0ff6377a971b193`.
The original global authority CIL and historical receipt remain unchanged until
the next explicit owned fixture installation. Fresh source2 verification follows.

Source2 freezes1500 files at `86f3d4651378b788e44c09e11f695d6422e40af0d34dd0d2fb26a120e31d9819`.
Matching .46 native/.47 rootless shared pinned UBI10micro artifacts and actual
no-runtime-Node probes pass. Strict gate3 retains its original exit1 after
backend and3908 component tests pass; the real API browser roundtrip case
expects350 models while the actual expanded corpus validates372. Only that
independently verified test assertion is being corrected; shipped source stays
byte-identical. Initial source2 native cohort `8dd86a73406f4fa69fd5f4cef0021da3`
passes all11 Chromium cases, including actual confined original-pidfd stop with
backend continuation, but fails when the coordinator sees a completion filename
before Node writes its bytes. All original roles drain,5 cgroups are empty,
5 endpoints refuse, verify timer remains inactive/unenabled and original evidence
is unchanged; original RESULT remains false with cleanup_unknown:false. The
ignored fixture publisher now exposes the completion name only after durable
bytes using no-replace linking. A fresh cohort must preserve and compare every
prior terminal receipt, outcome, pending SDK handle and predecessor. No replay or
acceptance is inferred from either failure.

The sole stale350→372 browser expectation now passes14 real API read checks
at both prefixes (22.531s). Final source3 is
`8112e6ca359767aa939190d9f78e03fe26249b8a666fff71c68de0c77de59095`/1500 files.
An exact all-file hash/mode comparison proves that only this unshipped assertion
changed from S2; every runtime, packaging, contract and user-guide input remains
byte-identical to the .46/.47 artifacts. Source3 strict gate4 is running. The
fresh native cohort `94d5a5903a69484b9a1a18f06546865e` uses the same installed
artifacts and captures all first-attempt terminal receipts, helper outcomes,
predecessors, journals and evidence before admitting new, independently keyed
intent. It requires their exact metadata/SID/byte equality at closure. Original
failed results remain unmodified. Rootless15 follows only after native33 success
and known cleanup on this same runtime source.

Concurrent read-only review finds one ignored collector defect before the current
native run finishes: the predecessor loop shadows its `prior` inventory argument,
so its final journal-delta join will fail after browser completion. The running
script remains unchanged. Do not replay passed operations to repair collection.
If the33 actual cases pass and the sole collector failure is this KeyError, a
separate corrected read-only join must revalidate original report/receipts/HMAC
outcomes, saved inventories and actual original-role drain. Preserve the original
false/unknown flags and cite the distinct qualification; absent that complete
proof native acceptance remains incomplete.

All33 current native browser cases pass in cohort94d5a590… (1251.273s
original wrapper). Its original false/cleanup-unknown RESULT and rc1 remain
unchanged: the sole collector failure is `preservation:KeyError`. Separate
corrected read-only joins and independent closure now PASS; evidence
`source2-native-independent-qualification.json`, SHA256
`0ef76e6f9aa601d2387ff9cf9c3415d5b29ec071457dcedc7c642031594e60c0`,
and qualified completion `f9285cf97a6dc48970c99069f409f38f657a15bb82fb0f04dd1d609d1eff5046`
under `/var/tmp/web-018-validation-blcl67j1`. The exact56 original files are
retained locally. All39 tracked processes are independently gone; the original
stop snapshot has38 because a fixed timer read appends one tracked child after
that snapshot. Its sole additional PID/start pair is281501/16331940, independently
gone; source attribution is recorded without a historical live-argv claim.
Five cgroups are empty, five endpoints refuse, all prior inventories/SIDs/bytes
match,24 host admissions/3 scheduled syncs/1 verification prelude join exactly,
436 requests are trusted and66 CSP checkpoints are clear. Historical unsaved
fixed-input full metadata remains an explicit evidence limit; the original
comparisons passed before the sole collector error, and current hashes are
independently bracketed. No job is replayed or failed original record promoted.

Strict gate4 exits1 after8926 passes/1 failure/52 unrelated deselections
(1659.942s; zero source drift). An older card-preservation test incorrectly
includes access time across intentional reads, which crosses one second. Only
unshipped assertions are corrected to compare preserved dev/inode/mode/uid/gid/
nlink/size/mtime_ns/ctime_ns and exact bytes; runtime safety is unchanged.
Gate5 is intentionally interrupted early to correct the same full-stat pattern
in all three assertions of that test module. Its actual rc1/113.938s and pytest
interruption teardown error remain retained, with zero source drift; it is not
acceptance. Final source freeze/full gate remain required.

Rootless transfer succeeds, but preload/stage1 refuses before staging because
SSH starts in a0700 fixture home inaccessible to the existing hfcache account.
The existing engine itself needs no change. A corrected private launch uses cwd/
and feeds the verified OCI through stdin; no directory permission, engine or
storage setting is changed. The original failed record is retained. Rootless15
and the final strict gate remain required before completion.

## Completion evidence

Completed 2026-10-27, WEB-018, this commit. Fixed schedule validation/change,
original-process observer stop and bounded journal routes now use the narrow
helper, separate bounded host runner and original-key outcome reads. Decision156,
INV022 and amendments to decisions109/115/121/135/136/141/145/150/154 record the
lane, MAC, authority, retention and no-replay boundaries. HostStatus1, REST bearer
and fourteen-tool read-only MCP compatibility remain intact. No runtime dependency
was added. Full rendered Administration forms are WEB-019.

Final source5 is
`415d9b7376c30b938e2739dee02525994aa03d4f1fcff06b35119e82d13b6320` over1500
regular inputs. It differs from actual artifact/runtime source2
`86f3d4651378b788e44c09e11f695d6422e40af0d34dd0d2fb26a120e31d9819` only in
two unshipped test files: independent corpus count350→372 and all three card
stat assertions excluding read access time while preserving nine identity/
mutation fields and exact bytes. All runtime, packaging, contract and human-guide
inputs/modes are identical; no artifact rebuild is represented as performed.
The full card module passes61 cases/12.77s; the corrected actual API browser
fixture passes14 cases across both prefixes.

`historical gate invocation (original command SHA-256 `b9d97947112e6e5c5005002b465c3dd68f8bd158ca8c41cb5966f57422999103`; Git `c692d7ae4b866fefd8a743a21afdb729da0f39c4`)` gate6 passes0 in
1813.441s with zero source drift:8927 backend tests/52 unrelated opt-in
deselections,3649 web unit/3908 combined frontend tests,581 historical frontend unit/110 mounted
checks,175 generated transport definitions, all three installed wheel profiles,
required build/browser/API-read/documentation checks and zero required skips.
Line/branch coverage is94.90%/90.11%;217 human documents and27 helpers align.
Original failed/interrupted gates and focused-test evidence remain retained.

Actual installed source2 acceptance covers48 once-per-engine cases:33 native
through existing Caddy22443 and15 rootless through existing Caddy8443, all using
trusted TLS, sandboxed Chromium156.0.8078.4/Firefox157/WebKit27.2 and Enforcing
SELinux. Native33 pass in1251.273s, with its original collector false/unknown/rc1
retained and separately qualified by corrected read-only joins and independent
closure; no operation is replayed. There are24 native host admissions,3 real
scheduled syncs and1 real verification prelude; original SDK pending files,
pidfd identities, HMAC outcomes and retained predecessors join exactly. Native
has436 trusted requests/66 clear CSP checkpoints. Rootless15 pass normally in
203.947s with9 denied POSTs/0 admissions,49 trusted requests/30 clear CSP
checkpoints,40 original stop identities gone,4 empty cgroups/4 refused endpoints,
exact created-secret retirement and all old/archive/API-worker/key/configuration
state preserved. Effective protected denials remain independent of Basic grants;
verification scheduling stays inactive/unenabled and no user-manager fallback
or general service control is introduced. HOST04–09 are complete in the ledger.

Matching native0.2.46/rootless0.2.47 source/wheel/UI/shared API-image artifacts
retain verified pinned UBI10micro ancestry and actual no-runtime-Node/package-
manager probes. Native/rootless image IDs are `76dc94fb…`/`1ad6a715…`; UI manifest
SHA256 values are `d67dc480…`/`2d5c55f1…`. Rootless reuses the existing engine and
Caddy image. The unindexed test-only host UI copy is retained outside the closed
release; canonical release verification passes without relaxing its index.

The original failed rootless startup remains false/unknown. Separate exact
closure proves its15 recorded processes gone, quiet units, empty cgroups,
refused endpoints and no role containers before retiring only its six created
secret IDs and creating the missing canonical root:983/0750 runtime parent with
its existing label. The subsequent15-case run is fresh and passes normally.
Partial-preparation originals, all prior failed records, every SDK handle,
WEB017C ambiguity and damaged predecessors remain preserved. Unsaved historical
full metadata for the earlier partial actions is explicitly not fabricated.

Evidence aggregate:
`/var/tmp/web-018-validation-blcl67j1/source5-functional-all-summary.json`,
SHA256 `dbad3dfc31cf69e6b056812d4c64aeb6001262bf233e2cfa837c10828f03f12e`.
It pins the strict gate, exact artifacts, native qualification, actual rootless
RESULT/report, test-only equivalence and original failed evidence. This is
owned LOCAL_STORAGE_SIMULATION, not live NAS or production/platform acceptance.
Administration/deployment/troubleshooting human guides and the API/server/
security/schema/host/script/container/operator contracts are updated with the
feature. Final bookkeeping checks pass: documentation alignment217/27, nine plan/ledger checks(0.88s), whitespace checks and all1500 frozen hashes/modes unchanged.
