# WEB-007: Expose safe installed configuration and exact managed-edit validation/preview

Interface-only instructions and source references have been omitted from this
retained shared record. Exact original text remains in Git `c692d7ae4b866fefd8a743a21afdb729da0f39c4`;
original document path SHA-256 `b225ae0b4f670f0edf95c06d9593b1f7eccb590bf5596e74886b69f7eba9ac13`,
original content SHA-256 `b1f537e207289c2364dfd1496b743c73ed5d2d1c328ad22bafc1947016ddd2c5`.
Historical proof hashes identify the original artifacts, not this edited record.

| Field | Value |
| --- | --- |
| Status | complete |
| Plan | [Web UI replacement](../2026-10-20-plan-web-ui.md) |
| Phase | P1 |
| Depends on | [WEB-006](web-006-guarded-host-adapter.md) |
| Branch | `feat/web-ui` |
| Work-package commit | `WEB-007: expose safe configuration and exact managed previews` (this commit) |

## Read before implementation

Also read the relevant sections of [architecture](../support/web-ui/architecture.md), [API contracts](../support/web-ui/api-contracts.md), [testing strategy](../support/web-ui/testing-strategy.md), [acceptance matrix](../support/web-ui/acceptance-matrix.md), and [human documentation map](../support/web-ui/documentation-map.md). Load only affected living contracts and ADRs through their indexes. Refer to the [source review](../support/web-ui/source-review.md) for pinned baseline evidence; current git wins over it.

## Scope and implementation requirements

Implement GET /config with nonsecret editable projection, protected-field descriptions and opaque full-byte base revision. Never publish a secret-bearing raw hash or sanitized placeholder document that can overwrite real configuration. Keep reads read-only even when candidate/lock files are absent. Define a strict typed managed-edit representation that can add/update/remove model/dataset entries and supported nonsecret global fields; preserve hidden/protected fields server-side and tag-only identity.

Extend existing validation and planning requests with the exclusive managed-edit form, retaining installed/literal candidate request and response compatibility. Reconstruct exact candidate bytes through one backend service and include versioned assessment/preview identity needed for application. Bound edits, strings and serialization before allocation. Reject authority-changing edits that cannot be safely installed under startup-pinned root/UUID/Hub/credential authority. No browser path/token/source override.

Plan/validate are never installation. Snapshot under the existing config guard where needed, release locks before Hub preview, and later compare exact base identity. Preserve domain warning/error results and compatible-authority distinctions. Define serialization behavior and comments/formatting expectations; use a justified maintained TOML writer/round-trip library if needed rather than regex rewrites.

## Unit and component validation

Test field constraints, normalization, tag-only base changes, opaque-token scope, hidden-field preservation, malformed/coercive/mixed bodies, deterministic exact reconstruction, unsupported authority changes and secret-safe output.

## Integration validation

Call real config read/validate/plan through API/helper with installed and candidate fixtures. Race two readers/editors and change base bytes without changing policy fingerprint; verify stale refusal. Test CLI literal candidate behavior remains unchanged.

## Functional validation

Through Caddy, read config, submit valid/invalid/tag-only candidates and sizing previews, observe exact classified results and protected fields. Lost preview observation retains original operation identity and does not install anything.

## Human documentation deliverables

Start configuration-and-tags guide with projection/advanced-view limits, normalization, validation versus preview, conflict handling and authority-changing manual procedure. Update API/config/server schema and examples.

## Acceptance

The UI has a safe complete editable source with full-byte concurrency protection; existing candidate clients work; preview is exact and non-installing; protected authority and secrets cannot be changed via redacted fields.

Historical execution summary: the recorded gate included the retired interface; exact invocation and original proof remain in Git `c692d7ae4b866fefd8a743a21afdb729da0f39c4`.

## Execution notes and blockers

Started2026-10-25 after WEB-006 commit `9af58cb` and a clean checkout.
Reviewed the configuration/helper/API/operation contracts, INV001/002/018/020/021,
ADRs119/122/138/139/141/150–152 and bundled architecture, test, acceptance and
human documentation requirements. CONFIG01–05 remain pending.

Use the existing fixed config-read/opaque HMAC boundary and add read-only
config-prepare. A bounded renderer for the closed schema1 scalar/table/array
vocabulary reconstructs complete TOML from parsed server-side data; it never
rewrites source with regular expressions. Comments/formatting are deliberately
canonicalized. This keeps the protected host helper standard-library-only;
no TOML runtime dependency or frontend executable is added. The exact decision,
public/private schemas and required scope are recorded before implementation in
ADR153 and the living contracts. Apply and private persistent staging remain
WEB-008. No production effects or wider host command authority.

## Completion evidence

Completed2026-10-25, this commit: the strict source gate and both installed
profiles pass. CONFIG01–05 are complete with actual source and functional mappings.
The commands/results below distinguish source checks from installed evidence.

Current source progress: strict managed DTOs preserve the old installed/literal
request canonicalization;104 focused model/candidate tests pass. The protected
stdlib reconstruction/protocol/client slice passes362 focused tests, Python3.12
syntax, lint/types and independent review. Twenty real ASGI/operation-store tests
pass (13.74s), including original planning services with an owned upstream adapter,
empty/no-Hub assessments, bearer denial before helper access, protected-field
suppression, stale full-byte base after queue waiting and original-handle recovery.
These are source/Unix/API fixtures, not installed functional acceptance. Public
wire/client integration and human guides are implemented; the strict source gate and native same-Caddy installed tests now pass.
The rootless functional run remains pending. The owned HTTPS Hub fixture uses real metadata/
dry-run protocol and trusted TLS, with no API/business-service mocks.

First full strict gate is honestly failed:1,065.517s,7,980 Python passes,
two failures and52 documented opt-in deselections; all1,372 frozen file hashes/
modes stayed unchanged. Both failures are the independent security route inventory
missing GET/config, with no application failure. The inventory now includes it
as an administration-only read and explicitly updates the route count; focused
route-security coverage is rerun before the next full gate. Original log/result:
`/var/tmp/web-007-validation-yc95plp8/strict-gate{.log,-result.json}`.

Current build artifacts pass stock UBI10 micro foundation and an actual runtime
byte audit:110 package files/six UI files match source/wheel, no Node/pnpm/npm/uv.
Owned fixture metadata alone sets version0.2.4 (canonical product remains0.2.2),
with native0.2.4/rootless0.2.5 staged while preserving the older test releases.
The stock image is `5a3271936adbeb97d4aa1c19dab857924ef7928d1089854e5fe5aaaf751275a1`.
The separate unshipped Hub functional image `286c2a2ca75d9483c30942245238f0d2085f1cf99998a2ef6496fa7ccca72246`
adds exactly one public test-CA bundle layer; it does not claim the stock CA-byte
check. Before staging, the owned guest was independently observed drained, Enforcing, with
five original infrastructure identities alive, old selector0.2.2/releases0.2.2–3
retained and no active test credential aliases. No production action follows.

Gate two also remains failed:1,030.259s,7,980 passes/two failures/52 opt-in
deselections, no frozen-source drift. The newly inventoried admin read exposed
a related MCP acceptance expectation hard-coded to host/status. That test now
uses the shared administration-read inventory and requires the same403 denial
for config reads, preserving bearer/MCP authority. The combined REST/MCP/API
slice passes460 tests in119.80s. Gate three then ran under
`/var/tmp/web-007-validation-yc95plp8/gate3/`, snapshot
`f6adf0e8fdcd65cbe6fa8293f185ef5429ab2626648d879bf114c90f47532363`.
Only those two test files changed across the failed gate corrections;
application/wheel/UI bytes remain unchanged. Installed source has the first
explicit test-only inventory refresh; subsequent source inventory records the
actual transferred contents and the separate native public-CA unit fixture delta.

Gate three fails after1,303.223s with all1,372 inputs unchanged:7,982 Python
tests pass,52 documented opt-in deselections; locked wheel profiles,572 historical frontend
unit/110 mounted Firefox,2,826 web unit/2,886 combined component and both shell
browser tests pass. Combined coverage is95.11%line/92.52%branch/92.26%function.
The final real-API React fixture has one stale independent corpus-count assertion
(expected308, actual342); its other six root-prefix checks pass. Correcting that
literal preserves the independent exact count. The entire affected real-API
fixture then passes both prefixes in19.517s. Original failed gate and corrected
fixture logs remain under `/var/tmp/web-007-validation-yc95plp8/`.

Gate four fails at documentation alignment after10.587s, before pytest: an
ADR status link to the agent task violated the human-document boundary. The
status now states accepted design without an execution-record link; the
209-human-document/27-helper alignment check passes. Its retained snapshot is
`a0837df6dbf01e768abd28c92417c30cfb2b453975e5843e2c608ebbfd2679a2`.
Application and fixture-image bytes remain unchanged; the source change is the
browser assertion plus ADR153 conformance navigation wording. The installed
fixture source truthfully retains its earlier test/ADR snapshot; its actual
1,377-file inventory is `a7271f16943139ee6656ebaf2bfd6d7a8f54eb9d1885ee340a76ecd6a4c62390`.
Both releases/UI and the real HTTPS Hub fixture are prepared in the reused owned
guest with Enforcing policy unchanged. Initial root-coordinator manifest
validation refuses the public source's UID1000 private scratch ancestor before
service effects; the private coordinator now recognizes the fixed browser owner
without changing production validators. Gate five uses snapshot
`0ca1a8dc7461e5ee6b4283656d18ac7d8a4f625819a697ea0c64ee0602bc605b`.

Gate five now ACTUALLY PASSES in1,366.734s:7,982 Python tests,52 documented
opt-in deselections, all three locked wheel profiles, strict historical frontend and web
checks, both shell browser tests and the complete real-API React read fixture.
All1,372 frozen source hashes/modes remain unchanged. Original log/result are
`/var/tmp/web-007-validation-yc95plp8/gate5/strict-gate{.log,-result.json}`.
This establishes source conformance. Native functional acceptance below now
passes; rootless functional acceptance remains pending.

Earlier installed native attempts remain failed and retained. First25.812s
run passes every legacy candidate/permission/original-ID assertion, then the
browser cannot start because the newly copied root-owned public manifest was
not prelabelled. All application roles stop; the exact never-started created
browser ID is captured and retired without force, and original credential inodes
are preserved. Second83.171s run starts/drains all three sandboxed browsers,
but an initial test assertion incorrectly expects a nonnull configuration-read
wrapper fingerprint. The actual200 config projection is valid; its full-byte
`base_revision` is distinct from the operational fingerprint. The corrected
driver explicitly requires null in that independent read wrapper and obtains
the operational fingerprint through a separate existing installed-validation
call. Both failed original reports/generations and false flags are unchanged;
credential retirement passes. Later native results follow; no application,
image, policy, permission or confinement change was needed.
### Installed evidence and retained attempts

Native cohort `8b17eb1122594a2ab52be7661272708b` ACTUALLY PASSES457.793s:
all36 cases across Chromium156.0.8078.4, Firefox157.0 and WebKit27.2, zero required
skips/internal retries, real built UI/shared Caddy/trusted TLS/installed API and
helper. Validation, exact model+dataset Hub sizing, all old forms/capabilities,
original-key lost-ack recovery and three real tag-only stale409 races pass.
Original process/cgroup/endpoint/input closure passes; native credential inode
preservation follows. Local summary
`/var/tmp/web-007-validation-yc95plp8/native5-SUMMARY.json` is190718bytes,
SHA256 `2ce03eaf5bc80f805df85b01aecf54a1c0c490202bc9d44f7553cd2ecbd104f9`.
Unit/integration and this native evidence are mapped to actual CONFIG01–05 nodes;
those cases were still pending for rootless at that checkpoint.

Retained native3 timeout201.388s and native4 failure473.380s are fixture failures,
not acceptance. Native3 completed real previews and one external race before its
180s batch budget expired; that original predecessor remains retained. Native4
passes33/36 cases but the race writer correctly refuses reusing the prior
`race-chromium` tag. The corrected test derives tags from browser+cohort and keeps
all concurrency assertions. Hardlink publication cost is correctly0, rather
than the fixture's earlier fictional13-byte expectation. Measured multi-RPC
cases justify60s per case/900s per36-case browser batch; product limits do not
change. Bounded append-only progress makes partial outcomes observable.

Rootless first startup fails6.102s before helper/application start because native
cleanup preserved the old empty secret store, and Podman recreated its directories
as `container_var_lib_t`. Existing policy requires
`hfcache_host_helper_secret_t`. The original `cleanup_unknown=true`/false acceptance
flags remain unchanged. A separate retirement proves inactive services, all13
original children gone, five baseline processes alive and exact-six-ID ownership
before opaque backup/sync/nonforce retirement and inode preservation. New empty
store directories receive the existing persistent labels before further startup.
No permission or kernel-policy change is made.

Rootless second run starts correctly, then fails65.531s on installed validation.
Its original HTTP response was not retained. The actual source/runtime combination
is independently reproduced as `HFARG002`: stock rootless supplies a token file,
while the fixture had configured Hub authentication disabled. The fixture now uses
optional authentication and an owned TLS Hub `whoami` endpoint; source runtime
arguments and credential protections remain unchanged. The native disabled-token
profile retains its original passing evidence. A1.120s fixture-upgrade failure
attempted a cross-filesystem public-counter rename; the original remains intact,
and completion copies it without replaying earlier preserved writes.

Rootless cohort `77a9aceb881b4a50a41df2c3579fc6a9` then runs484.570s:
33/36 browser cases pass, including real tag conflicts and operation recovery.
Only the three Hub sizing cases fail with recorded `HFHUB001`/network unreachable.
Both the guest and original user manager lack a default route. The original QEMU
network is positively verified `restrict=on`, IPv6 off, loopback-only SSH forward;
external connectivity remains blocked there. A normal guest default route supplies
stock pasta routing without changing source, runtime arguments, privileges or
isolation. The corrected rootless run is recorded in final acceptance below; this failed
cohort is not promoted.

Focused API coverage remains90% (141 statements,11 missed,24 branches/five partial)
for unchanged API source `fa1673a7750a46e4af298ef2f62251e990c188812ffa809a8da0453a55d90d8c`;
retained data/export/provenance are in the validation directory. This is focused
coverage, not a claim that the full gate ran with Python coverage. The documented
managed duplicate-POST exception is reviewed against the default idempotency rule:
fresh base/policy checks may refuse a duplicate, while original GET observation
remains available. One supplemental ASGI/store test passes9.50s with tag drift,
same policy fingerprint, duplicate409, original lookup200 and exactly one receipt;
no enqueue or replay occurs. Existing literal/installed behavior remains unchanged.
### Final acceptance and handoff (2026-10-25)

Rootless cohort `d9c434c21c3144e28c1f9c8eb79fceb0` ACTUALLY PASSES493.939s:
all36 cases/three pinned browsers, zero required skips/internal retries, original
mapped API peer/manager, installed services/helper and real shared Caddy. Its
summary is203868bytes, SHA256
`93f5a4390e9b951fdccce560a9241cd38e59de68126fdb079e95d8e50f121c58`,
retained at `/var/tmp/web-007-validation-yc95plp8/rootless5-SUMMARY.json`.
All configuration/normalization/authority/legacy/sizing/opaque tag-race and original
operation recovery checks pass in both profiles. No API/business service is
mocked in installed acceptance; only the external toy Hub and loopback synthetic
NFS are fixtures. This establishes no live NAS or real-account acceptance.

Final retirement and normal Hub stop pass2.726s. Exact six original test secrets
are opaquely backed up and synchronized before nonforce removal; original Basic,
Hub, encrypted-credential and empty-store aliases are preserved without replacing
an existing destination. Both original stopped generations/results remain
unchanged. All application/helper/Caddy/browser roles are drained, endpoints
refuse, and the five original infrastructure PID/start pairs remain alive.
Original HMAC key, helper unit, CIL, installation receipt and compiled kernel
policy remain unchanged. The helper bootstrap was deliberately upgraded to the
matching application code earlier, with predecessor files preserved.

Stopped Hub counters record native/retained v1 aggregate7HEAD+14info+14tree per
repository type, and rootless v2 aggregate3HEAD+6info+6tree per type, with zero
payload GETs/bytes. Remote whoami count is0 for the optional/no-expected-account
profile; authenticated whoami is separately tested locally, never represented
as real-account proof. Original v1 runtime counter remains in place and is copied
privately; v2 uses a new filename. The owned VM retains the normal route behind
QEMU's restricted network for subsequent package tests.

Human configuration/tag guide and navigation, API/configuration/server/schema/
host/security/container/script contracts, invariant register and ADR index align.
Review covers INV001/002/018/020/021, AD01/15 and ADR119/122/138/139/141/150–153.
ADR153 records the closed stdlib renderer and narrow read-only lock amendment;
ADR141 links it. No runtime dependency or archive durable-format change is added.
The final source gate hash/modes remain valid; subsequent edits are the five
explicitly excluded plan/evidence/progress bookkeeping files. Documentation,
plan/evidence parsing and final whitespace checks run before commit.

Final bookkeeping checks pass: documentation alignment209human/27helpers; plan/
evidence parsing9tests in6.06s; whitespace clean. All1,372 checked source hashes/
modes still exactly match the passing gate; only its five declared bookkeeping
exclusions changed. No required work remains in WEB-007.
