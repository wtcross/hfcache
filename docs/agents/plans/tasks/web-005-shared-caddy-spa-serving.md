# WEB-005: Serve authenticated assets through the existing Caddy and build the real functional harness

Interface-only instructions and source references have been omitted from this
retained shared record. Exact original text remains in Git `c692d7ae4b866fefd8a743a21afdb729da0f39c4`;
original document path SHA-256 `39d327142cf6ee94e5e657ae11bcbadf2482893f87f2e8935d83eb663d2a53d3`,
original content SHA-256 `a0e09d7b5004b7a73108787fac60b0de848150e807002c3cb4f1b5e93b0e1b5e`.
Historical proof hashes identify the original artifacts, not this edited record.

| Field | Value |
| --- | --- |
| Status | completed |
| Plan | [Web UI replacement](../2026-10-20-plan-web-ui.md) |
| Phase | P1 |
| Depends on | [WEB-004](web-004-basic-auth-and-permissions.md) |
| Branch | `feat/web-ui` |
| Work-package commit | `WEB-005: serve authenticated assets through existing Caddy` |

## Read before implementation

packaging/containers/Caddyfile.in and server.toml.in; app lifespan/outer middleware; architecture deployment/static root; existing test socket/lifespan fixtures.

Also read the relevant sections of [architecture](../support/web-ui/architecture.md), [API contracts](../support/web-ui/api-contracts.md), [testing strategy](../support/web-ui/testing-strategy.md), [acceptance matrix](../support/web-ui/acceptance-matrix.md), and [human documentation map](../support/web-ui/documentation-map.md). Load only affected living contracts and ADRs through their indexes. Refer to the [source review](../support/web-ui/source-review.md) for pinned baseline evidence; current git wins over it.

## Scope and implementation requirements

Implement optional app-owned UI static serving from an explicitly configured immutable asset root and independently versioned bootstrap context. Expose P/ui/ navigation/assets and preserve P/api/v1 and P/mcp under the same Caddy instance and existing Unix upstream. Retain Caddy TLS/auth-header/streaming/no-admin/no-ACME/no-archive boundaries. Do not add global Caddy Basic or another frontend server.

Validate asset manifest/paths/bounds/identity and isolate UI history fallback from missing assets, API/MCP routes and non-GET methods. Preserve native Unix prefix behavior. Implement safe base path/runtime bootstrap and strict headers/cache policies without inline script or externally loaded assets. UI-disabled deployments remain compatible; enabled missing assets produce explicit startup refusal. Query a safe UI contract/build identity without changing /capabilities.

Introduce the provider-neutral real functional runner and --with-web-functional gate scaffold with application/platform profiles. It owns test Caddy, CA, browsers, API, fixture state and finite cleanup. No test shortcut disables TLS or production guards. Early suite runs the completed routing/auth cases and clearly reports later feature cases as pending; final strict acceptance will require all cases.

## Unit and component validation

Test route classification/fallback, MIME allowlist, asset traversal/symlink/unknown manifest, startup enablement, bootstrap escaping, paths/prefixes, security headers and script runner unsafe workspace/prerequisite refusals.

## Integration validation

Run real Caddy TLS -> API Unix routing plus concurrent lifespan/prefix requests. Confirm one app registry/pool/worker relationship, unchanged bearer REST/MCP endpoints, and bounded static serving on disconnect.

## Functional validation

Run Chromium/Firefox/WebKit login, deep-link refresh, root/nonroot prefix, missing JS 404, API typo and MCP errors never HTML, rejected plaintext/untrusted certificates, and REST/MCP bearer calls on the same Caddy origin while a Basic browser is active. Inspect browser network to prove no CDN/other origin dependency.

## Human documentation deliverables

Write user entrypoint/navigation and operator shared-Caddy deployment/prefix sections. Update containers/server/API security boundaries and development/script references. Document exact unavailable/missing-assets messages.

## Acceptance

A built authenticated SPA works through the existing Caddy topology with real trusted test TLS and no bearer regressions; route/security tests pass in three engines; the reusable functional harness is fail-closed.

Historical execution summary: the recorded gate included the retired interface; exact invocation and original proof remain in Git `c692d7ae4b866fefd8a743a21afdb729da0f39c4`.

## Execution notes and blockers

**Common21 actual start (2026-10-21UTC):** reviewed rootless21 installer
SHA256 `6f84e4a23af177f507559b4e1eb7ebd1bdda1cc3ad87ef953eb955a619982ac8`
actually exits0/reaped74788, log SHA256
`ae0e056204d418f8f3d39ec0549c8c58e2300d8c8145daa3a5f122e85195df24`,
control SHA256 `a1e011325e3836150519127bba9684ae199ce9667a177ea1531bbeca6ea02b57`.
The original canonical `--profile all` invocation starts
2026-10-21T10:46:36.459287UTC, caller60032/start5697770/UID1000, host session40789;
log `.scratch/web-005-common21-all-functional-v1.log`. Actual manifest21
`050b4abb1e1f9813417e6f6705779d4678a38f4808ab40696f6edb9b0c5e8379`
and native20 control
`b53e6816570e0d846c78048186bb395c5b1eb4a959e0413dccbd24579051afb2`
remain its authorities. Final-bound installer source checks pass6/zero skips;
these do not establish runtime acceptance. All six functional outcomes, monitor
success, normal closure/audit and the separate runtime13-to-host14 compatibility
receipt remain pending. Frozen source14/gate14 and guest13/artifact4 provenance
are unchanged; common20 failed/UNKNOWN/HOLD records remain intact.

**Explicit resumption (2026-10-21):** Tyler resumes with “continue”. The
paused dated plan/current selector are reactivated at WEB-005; the pause checkpoint
below remains historical. Git still has the uncommitted WEB-005 work above
`24625fcd009125554e0248cfc0cf5f00d5e53f6e`. Gate14's actual completion audit
SHA256 `d80896c63f824cffb9ade963ed611481422bd5a346ef3c57538f311323b174d4`
is reconciled with its retained result/log; all1310 host source14 hashes/modes
remain unchanged. Source-only acceptance is positive, while required installed
all-six/normal closure remains blocked and no future task/case is promoted.
Common21 manifest/native20 provisioning are the recorded actual successes;
rootless21 binding/provisioning and functional execution remain pending review.
Guest source13/artifact4 and common20's failure/UNKNOWN/HOLD remain unchanged;
a fresh common21/runtime13-to-host14 compatibility receipt is still required.

**User-requested pause checkpoint (2026-10-21):** the plan is paused and the
selector has no active task. WEB-005 stays in progress, uncommitted and blocked on
required installed acceptance; it is not complete and no successor is activated.
Host source14 remains frozen. The already-running
`historical gate invocation (original command SHA-256 `dfe15d4ee16e8207e5ddfe1138f7416950f8e6013a5d77e8aa230bfd51dccdc4`; Git `c692d7ae4b866fefd8a743a21afdb729da0f39c4`)` gate14 exits0/reaped at
2026-10-21T10:40:34.430894UTC in1202.869seconds, all1310 hashes/modes unchanged.
Actual results:6643Python/52default deselections; three locked wheel profiles;
572historical frontend unit/110mounted;2756web unit/2805combined;21sandbox/9functional
metadata;2preliminary browser/14real-API read checks. Required checks have no
skips/retries; coverage95.61%lines/92.83%branches. Log SHA256
`49b76ee0668f9a36a6549bdbf2861c0e84d8680cd33cc9b28ca25f75931354fe`.
The independently reviewed completion auditor exits0 with empty stderr,
rechecks all1310 files/modes and seven closed processes, receipt
`.scratch/web-005-fourteenth-gate-audit.json` SHA256
`d80896c63f824cffb9ade963ed611481422bd5a346ef3c57538f311323b174d4`.
This is source acceptance only. Guest source13/artifact4 provenance,
common20's failed result/original cleanup_unknown and every completion HOLD remain.
All already-running checks are finished; execution is paused with no new run.

Common21 manifest preparation actually exits0/reaped46066: manifest SHA256
`050b4abb1e1f9813417e6f6705779d4678a38f4808ab40696f6edb9b0c5e8379`,
fixture `0a1d1045-05ea-476e-ada1-b1adc5550cdd`. Native20 provisioning actually
exits0/reaped48477 with control SHA256
`b53e6816570e0d846c78048186bb395c5b1eb4a959e0413dccbd24579051afb2`
and no services started. Rootless21 is **uninstalled**; all common21 functional
execution is **unstarted**. Its unbound private templates remain preserved.
The last read-only final-thread projection exits0 (log SHA256
`3b2335291f1b3ec8816a8eb8e3a1ba762581e037760b2aa8a18716e943e47cff`):
original rootless final authentication-thread count0/no Basic HTTP, one dead
runner/zero metadata threads, exactly three pre-browser HTTP observations and no
browser intent. Therefore the final validator's mandatory authentication-thread
inventory cannot establish normal stopped acceptance before browser execution;
no extra fix or acceptance is inferred. Independent collector9 identity/schema
regressions pass18/zero skips; these remain source-only proof tests.

On explicit user resume, first reconcile final gate14/audit and retained read-only
results with git and these records. Then review the remaining proof preflight,
complete immutable rootless21 bindings/provisioning only within renewed active
work, and run the original fresh all-six invocation plus independent normal
closure audit. A separate common21/runtime13-to-host14 compatibility receipt is
required: the old `02acce42…` artifact bridge retains its unfulfilled common20
success condition and must not be rewritten or relabelled. No further preparation,
tests, guest effects, acceptance promotion or commit follows this checkpoint.

The authoritative original source13 ready validator isolates common20's refusal
at `role_evidence:3151` → `detailed_role_evidence:2701` → `origin_probe:2230`:
rootless worker schema2 publishes the full four-field proc identity, whereas its
existing closed wire proof requires only `pid`/`start_ticks`. All three actual
role/container checks precede this refusal. Private collector9 SHA256
`9080bcabde88f274cda765b49086c33c1f6656669da1c25f0371db680d503872`
corrects only that serialized pair; original full process/status/before-after,
policy/denial and Caddy schema1 observations are unchanged. Source-only regressions
pass18/zero skips; no installed correction is claimed. Source14/canonical runner/
tests remain unchanged. Fresh common21 manifests/controls are inert drafts only,
pending remaining proof preflight, actual pins and original required all-six run.
Common20 supplemental closure actually exits0/reaped:117 identities gone,
30 cgroups empty,11 containers stopped/PID0 and25 endpoints refused. Log SHA256
`9f2b50d3fc1e54974d508f88f107336f444b77644debdc7cd924a415ecb80873`
revalidates guest source13/all1310 files and four original normal results with
204 trusted+12 untrusted checks/zero skips. Original cleanup_unknown and
unexecuted sixth generation remain; completion20 drafts/auditor stay HOLD/ineligible.

Common20 actually exits1/reaped caller53981/start5428085 with valid monitor,
observed wait/identity closure and no monitor errors. Host log SHA256
`aad40a0b8a99b7418823450ed7058f679cb63f5e533fab7bf3e6a66f2ff735ed`.
Four original normal application/native root+management results precede
rootless/root `c92fbf827bfb431592d8b0ab49d76be5` failing before browser execution.
Its saved raw tcp6/udp6 rows at `::`:8443 match the new closed listener-family
predicate; no controller diagnostic or actual canonical failure stage is yet
established. Original cleanup_unknown remains; prefixed rootless is unexecuted.
Both conditional common20 bundles are on HOLD with original payloads/REVIEW/nulls
unchanged; completion-only auditor is unexecuted and ineligible. Source14/gate14
continues frozen. Diagnosis and supplemental physical closure remain pending;
no product defect, correction or full functional acceptance is inferred.

Host source14 actually freezes all1310 files with exactly nine approved prose
updates and unchanged modes. Inventory SHA256
`7eb4c9b8d72b8a5f7ff42cd69920b7c1fac92080a2640817aa4966d501e84607`, snapshot
`9257e274732ade779c2134980b627d99a62051e7c8a510073d96e5e80b68fce9`;
actual compatibility receipt
`02acce42c4229f8dff779207b276bf37787f628450678bf44e8408a6b07b0009`
verifies all1301 other source files, product/wheel101, UI44/two builds and exact
functional/private proof bytes unchanged. Artifact4 keeps source10 provenance;
original common20 runtime retains source13/manifest/control identity, with no
guest source mutation or relabelling. Gate14 actually starts
2026-10-21T10:20:31.561218UTC, PID2556677/start404657340, session19525. Its final
result and original common20 all-six/monitor0/independent audit remain pending.
Post-prose documentation202human/24helpers and all six migration tests pass;
the scoped docs-only correction changes no executable behavior or invariant rule.

Source13 gate13 actually exits0/reaped at2026-10-21T10:17:17.765626UTC,
1321.085seconds. Independent audit SHA256
`9f4d2f457360f9d274a3604fe79bf9614e23fc83bd1e40a7860199e4f6b85377`
records6643 Python passed/52 default deselections, three wheel profiles,
historical frontend572+110, web2756unit/2805combined, two preliminary+14 real API-read browser
checks and unchanged1310 hashes/modes; line coverage95.61%, branches92.83%.
Root then applies the exact approved nine-document prose patch, correcting stale
implementation labels without changing product/UI/runner/tests/builds or runtime
policy. Actual host file map matches proposed snapshot
`9257e274732ade779c2134980b627d99a62051e7c8a510073d96e5e80b68fce9`;
all modes are unchanged. Final source14 inventory/gate/compatibility bridge remain
pending. Guest source13 is untouched through common20's original audit, and its
functional evidence must keep source13 provenance. Common20 is active with no
final all-six outcome; source13/gate13 are separate measured evidence. No older
failed/unknown record or conditional completion draft is promoted.

Fresh common20 original `--profile all` actually starts
2026-10-21T10:01:39.618671UTC, caller53981/start5428085/UID1000, hostsession34205;
log `.scratch/web-005-common20-all-functional-v1.log`. Actual manifest SHA256
`07eee47bf17f58dd581316155ffc8bbcc971fa263a04ed659466e13e8f7b1f5f`, native19
control `9b6d4af75a5f820a6d1a02f7df0f2c594941aa78c986ce0389e39fbedcdce299`
and rootless20 control
`052efa80f4013118d0bbfa08dc338551a073f12a23da3eb6d87a87530fed708b`
are bound after both provisioning commands exit0/reaped, with no role started
by provisioning. The unexecuted original rootless template's two stale19
destinations are preserved; the corrected fresh template/provisioner uses20.
Source13/gate13 are unchanged; all-six normal results, monitor0, independent
audit and gate13 pass remain pending. Common19 completion drafts stay on HOLD.

Source13 is frozen at1310 files/exactly five authorized documentation/validator/
test changes. Inventory SHA256
`645bbd0231905ae5eb599fa45111f96e9c6f2f4ed40c4796e8fe26b97100676b`, snapshot
`d3530149a4f79bf5c53147b6561eeb7446ded8017eee5293a5a3691ff6be92d3`;
independent local recheck verifies all hashes/modes and the exact five-path delta.
Actual host artifact4 compatibility passes, receipt SHA256
`ce02f9e5046171c7fad71640248429a4206434d73505d1ab1dc8ea4f7376ab6f`:
101 package/wheel members and44 UI inputs remain unchanged, with original
source10 artifact4 provenance preserved. Source13 reconciliation actually exits0/
reaped session36859, verifies all1310 files/five updates and retains backups;
no installed functional acceptance follows. Gate13 actually starts
2026-10-21T09:55:16.680608UTC, PID2535611/start404505852, session73676;
gate13 completion and fresh common20 all-six acceptance remain pending.
Independent review `.scratch/web-005-source13-independent-inventory-review.json`
SHA256 `e0c1a364dd090d2ff5a87ea30fe10dbd2c88b1a4b83cba1c9faf3813dcc66738`
also reviews the exact guest/boot/SELinux/archive/previous-state guards and
fresh backup/atomic reconciliation. Conditional completion drafts remain on HOLD.

Source12 gate12 actually exits0/reaped at2026-10-21T06:58:57.953317UTC,
1255.446seconds:6561 Python passed/52 default deselections, three locked wheel
profiles, historical frontend572+110, web2756unit/2805combined, two preliminary and14 real
API-read browser checks. Independent audit
`.scratch/web-005-twelfth-gate-audit.json` SHA256
`aed3aa94455b802804357d854950523115f186bf4bc5c497a48c4a9f23828318`
rechecks all1310 hashes/modes, seven reports and seven closed processes. This is
retained source12 evidence, not installed all-six acceptance.
Common19 supplemental read-only closure actually passes:117 recorded PID/start
pairs gone,30 cgroups empty,11 containers stopped/PID0 and25 endpoints refused.
Log SHA256 `942dbaed6326ab252bbeed3cad4a805135501aaad2135cf5341faf1a63f8dc09`
also revalidates four original normal results/204 trusted+12 untrusted checks,
zero skips, source/package/assets/tools/seed closure and original failed
rootless cleanup_unknown. The sixth generation remains unexecuted.
Separate retained TLS3 listener projection SHA256
`28b5b1b01288d2c6420f1f7434130bf8a4ec047a87d34772eac79825d46ac3df`
binds both controlled arms' raw tcp6/udp6 rows at `::`:8443 to their recorded
processes. It supplies no missing common19 rows. Approved contract-first source13
documentation now admits only two closed raw rootless family forms; native
loopback, outer rootless loopback publication, strict TLS and all original
isolation/drain checks remain unchanged. Product/templates are unchanged.
Source13 freeze/gate13 and fresh common20 all-six acceptance remain pending;
all conditional completion drafts remain on HOLD.

Common19 actually exits1/reaped caller47665/start4171226 with valid monitor,
observed wait/identity closure and no monitor errors; host log SHA256
`e9276bfefe746dc024ad44d46f1ee9ce7324553257921f147a80d1c6cf4d5cd5`.
Four original normal application/native root+management results precede
rootless/root generation `88b3d4f54d3c4dab923fb4fbaf96c47e` refusing the private
`inspect:1828` INET-listener predicate after its preceding checks pass. Three API
HTTP events are observed, but no rootless browser/canonical ready/stopped proof;
original cleanup_unknown remains and prefixed rootless never runs. The exact
INET rows exist only in controller memory before this assertion, so the failed
operand is unmeasured. Retained facts/partial closure and a new isolated control
are pending; no address/family cause or accepted correction is inferred.
Source12/gate12 remain unchanged; the conditional common19 drafts are on HOLD
with their original final-result nulls intact. Its completion-only auditor is
unexecuted and ineligible. Fresh all-six acceptance remains required.

Gate11 exits1 after6560 passed/one failed test: the retained selector's relative
Markdown links resolved from its new task directory. Preserve original failure
log SHA256 `9fa8304716fa08d310b71230d011e97f3fb2f992f89d4e3af56ccdf5cb8ff4a5`.
Only three targets are rebased to the same resolved documents; labels, content
and history remain, with the exact original494-line bytes retained in ignored
scratch. Whole migration tests6/6, documentation202human/24helpers and whitespace
checks pass; evidence `.scratch/web-005-selector-link-relocation-checks.json`
SHA256 `c6b671fb9c520deea845dd9c3500f8e73acee997806ca1711bb58969d3ea81f0`
also rechecks all1310 source12 hashes/modes unchanged. Full gate12 actually
starts2026-10-21T06:38:02.507306UTC, PID2493278/start403322435, log
`.scratch/web-005-twelfth-strict-gate.log`. It and common19 continue independently;
neither gate completion nor all-six acceptance is claimed.

Common19 canonical `--profile all` actually starts2026-10-21T06:32:11.020827Z,
caller47665/start4171226/UID1000, fresh workspace
`.scratch/web-functional-common19-all-v1`; log
`.scratch/web-005-common19-all-functional-v1.log`. Manifest SHA256
`e7c43df5c7ae01fd6c3fdc69176d2d78f1e3f56ac59d80dbf2f88d888c351e3f`
binds native control18 `b7926462dd7e61b7418a3e34eab23285ec82c79cd52aa11ae61f54b21387d8f7`
and rootless control19 `87cfe2c515c3577fb36c0363b232b14e7e01b3d16b054964069acecb12d58cb6`.
Source12/gate11 remain unchanged; normal all-six completion and independent
audit remain pending. No feature case or task completion follows this start.

The original native18 installer refuses a stale private runner hash; preserve
that failed source. Read-only failure projection v1 separately refuses the
root-owned public wrapper's UID. Fresh v2 projection SHA256
`c57fb8f16debb38fbcdf4f3378bfa122fc19eba13c5da8c42371bc93170a278a`
actually confirms all seven planned destinations absent and five retained
files' hashes/modes unchanged. New immutable corrected native18-v2 and
rootless19-v2 provisioners then exit0 without starting roles; the corrected
runner guard is checked against the actual source12 inventory. Earlier
refusals and original cleanup_unknown records remain unchanged.

Source12 is frozen and actually installed: all1310 source files, exact five
authorized proof/docs changes, inventory SHA256
`086aff3c2d036208977fc908e3f342d0b645b955b01359d998055f1a8176ea54`,
snapshot `e857a8953e0606441dbad74e16fa601a2801af47d0cdcb3ae597942261ed6d13`.
Host artifact4 compatibility passes without relabeling its source10 build;
package101/UI44 remain unchanged. Gate11 actually starts
2026-10-21T06:18:02.528876UTC, PID2480225/start403202437, and remains pending.
Actual read-only retained-role projection SHA256
`34dad97408aada1606e9b4bcfb711a7c2dce4a0be085bea97ee9f744888f5e78`
confirms all three raw exact11-entry CapDrop lists, empty CapAdd and observed/
declared drop-ALL/no-add arguments. The strict raw-encoding/zero-capability
validator passes341 owner checks and87 independent selected checks without
skips. Earlier failures, source11/gate10 and original artifact4 provenance remain
retained; fresh private fixtures and canonical all-six acceptance are pending.

Common18 native17/rootless18 provisioning exits0 with no role/container starts.
Its attempted `--profile rootless` invocation is rejected by the unchanged
canonical CLI, whose choices are application/platform/all: caller47202/
start4002124 exits2, wait/reap observed, before workspace or role creation.
Log `.scratch/web-005-common18-rootless-functional-v1.log` SHA256
`969324ee5160c9f925b35c46a54f26de03a69537bd55c12a190fcaec5269caf7`
retains this preflight failure. A literal CapDrop metadata predicate remains an
unconfirmed fixture-validation candidate awaiting actual retained-role fields;
no runtime failure or acceptance is inferred. Fresh canonical all-six acceptance
remains required; source11/gate10 stay frozen/unchanged.

Read-only partial17v2 exits0/reaped after the retained v1 diagnostic refusal:
102 recorded PID/start identities gone,22 cgroups empty, six stopped browser
containers/PID0 and20 endpoint refusals. The three original normal generations
revalidate153 trusted/9 untrusted browser checks with zero skips; all1310 source
files, two101-file package trees,183 tools and11-file seeds remain unchanged.
Log `.scratch/web-005-common17-partial-postverify-v2.log` SHA256
`370f1d19ef88d8006ec479f6964ca39fa259b79e318fc989f7c57d02cc056d90`
retains this supplemental closure. The failed generation's missing controller
owner pair and original cleanup_unknown remain explicit. Private packet2's
strict bounded task-absence proof passes19 local checks and19 independent
checks; fresh installed acceptance remains unperformed. Source11/gate10 remain
unchanged; no old failed result is promoted.

Common18 manifest-only preparation exits0/reaped74626, retaining all1310 source
bindings. Manifest SHA256
`f2c5456f8abf315d2fe18805b10e05e4ed4120dd5a7bf72c6df7ff2a7e25d8d9`
binds fresh fixture `83d58be5-1c18-4c74-aa6c-9f24226c308b`; no role starts in
preparation. This establishes no runtime acceptance; fresh canonical all-six
acceptance remains required.

Fresh read-only failed-status projection narrows common17 to three original
normal results (both application prefixes and native/root). The fourth,
native-prefixed generation `80731eb0c80b409492721f489621288b`, fails before
API/Caddy start in private packet helper `close_listeners:656`: the second
kernel/proc task-TID absence assertion follows successful thread join and the
first no-errors/not-alive/closed-descriptor assertions. Its saved packet marker
is exactly aborted evidence, never schema2 acceptance. Observed worker status
is failed/1 with MainPID0 and empty cgroup; canonical ready/stopped/browser are
absent and original cleanup_unknown remains. Both rootless generations never
run. Projection `.scratch/web-005-common17-failed-status-v2.log` SHA256
`77ff232579de0d5ce44368104cf82ae4332b856b8cbfb6ea90a5c9c6b671005f`
retains the exact controller frames. Partial closure audit and a narrowly bounded
private-helper proposal remain pending; no product cause or accepted fix is
established. Fresh all-six acceptance is still required; source11/gate10 remain
frozen/unchanged and completion drafts remain unapplied.

Common17's actual monitor now exits1 and observes wait/reap of exact caller
42536/start3784257/UID1000. Metadata is valid, owned identity closed and monitor
error_classes empty; full acceptance is false. Completed host log
`.scratch/web-005-common17-functional-v1.log` SHA256
`e6981c14d8297b90bd1d50c136023c836de4be793da931cb83409ea681779024`
retains this failure. The final per-profile cause and cleanup evidence remain
undetermined at this checkpoint; a later read-only observer's packet-projection
schema refusal does not identify the feature failure. No SNI regression or
product cause is inferred. Completion/selector/ledger drafts remain unapplied,
and the completion-only all-six auditor remains unexecuted and ineligible for
this failed invocation. Source11/gate10/artifact4 stay frozen/unchanged;
required actual all-six acceptance remains unresolved pending read-only diagnosis.

Fresh common17 canonical `--profile all` starts2026-10-21T05:27:41.332912Z,
exact caller42536/start3784257/UID1000, recorded in
`.scratch/web-005-common17-functional-v1.log`. Manifest SHA256
`ee8a6bd314b8c946f0d4afb946d18c8fe3e460d42b6ab77d320c9452e30b979b`
binds native control16
`f302b019dcbb7415ac2e015054aed4c4a9f5396ef9fa1e39c7fdbd919c961963`
and rootless control17
`1cd57a60d9bc8fb98788678d47633a6e2b59e69dd3759c784f081b14bac8515e`.
Both immutable provisioning commands exit0/reap without starting roles.
The new rootless fixture template95ac1518…370e4 adds only fixed default SNI;
old templates/PKI/evidence remain. All six functional generations, original
monitor outcome and completion-only independent audit are pending at this start
checkpoint. Source11/gate10/artifact4 remain unchanged; no acceptance follows
from invocation or preparation, and common16's failure/unknown is not relabelled.

The isolated two-arm TLS-selection control v3 now exits0 and is independently
observed closed. Baseline records three TLSV1_ALERT_INTERNAL_ERROR failures with
no HTTP response; the sole TLS change, fixed `default_sni 127.0.0.1`, records
three strict CA/IP-verified TLS1.3 HTTP200 responses with the expected fixed
control body and the same original leaf DER. Both containers stop normally with
exit0/PID0, eight retained arm identities are gone, four cgroups empty, controller
gone and loopback33334 refused; original PKI inputs remain unchanged. Observation
`.scratch/web-005-rootless-caddy-tls-selection-v3-observation.json` SHA256
`9ee7bde543fc47d00cb5918d62b36774175586c0c625cf289ae14d2a44d8f2b0`
binds summary SHA256
`b7a2332727896d89dbad13e1a34621b6dced2156a7822dffbdb91dfe3f1066dd`.
This confirms certificate-selection behavior in the isolated fixture, with no
API/worker or feature acceptance. The minimal fixture-only template correction
is approved under the existing architecture/TLS contract; fresh immutable
common17 bindings and actual all-six acceptance remain required. Common16's
original failure/unknown and v1/v2 diagnostic refusals remain preserved;
source11/gate10/artifact4 and canonical contracts are unchanged.

TLS-selection diagnostic v2 also refuses before manager/process start or any
TLS attempt: actual Podman inspect expands `--cap-drop=ALL` into eleven named
default capabilities, while the diagnostic expects the literal list `[ALL]`.
Its sole baseline container remains retained in created state, not running/PID0;
no process/cgroup or treatment arm is started. The original diagnostic
`drained:false` classification remains. Read-only observation
`.scratch/web-005-rootless-caddy-tls-selection-v2-observation.json` SHA256
`e9281b2aa27ea6a690a1ebcb6d5f7c8334beeaee9dc6a25b655f6c51aeee48f7`
confirms the controller and six exact command identities gone after observed
waits, loopback33334 refusal and unchanged original TLS inputs. Preserve v2's
source/container/files. A fresh v3 is being prepared with the measured expanded
capability metadata plus actual live-kernel zero-capability checks; no SNI cause,
TLS positive or full acceptance is established. Source11/gate10 remain unchanged.

The isolated TLS-selection diagnostic v1 refuses before either arm starts:
its saved baseline adapter output has two actual TLS policies (explicit
SNI127.0.0.1 certificate selection plus an empty fallback), while the diagnostic
incorrectly requires one. Read-only prerequisite observation
`.scratch/web-005-rootless-caddy-tls-selection-v1-observation.json` SHA256
`240f40f030f04cb3c95d99c65471174523f1d59f396d8b6d96eb2f4272a43862`
confirms adapter exit0/observed wait, both recorded controller/adapter identities
gone, and all arm intents/CID indexes absent. Preserve installed v1 source and
partial diagnostic files; this is no TLS experiment or confirmed SNI cause.
An immutable v2 is being prepared to correct only the adapter-shape prerequisite.
Source11/gate10/artifact4 stay unchanged, and required all-six acceptance remains
unresolved.

Common16 supplementary read-only closure subsequently passes without replaying
start/stop:116recorded outer PID/start identities are gone,30cgroups empty,
11containers stopped and23owned endpoints refuse. Original canonical revalidation
passes the four normal generations'204trusted/12untrusted browser checks with
no skips. Failed rootless's three roles exit0 and API/worker resources drain,
while its original missing canonical ready/stopped/browser and cleanup_unknown
remain unchanged; the sixth generation stays unexecuted. Partial audit v1 safely
refuses because the failed CLI publishes no SUMMARY; preserved v2 reads the
five actual RESULTs without writing a synthetic summary. Its log SHA256
`ddf25132795059bcb0b96f83d108980ee8c6bfc2efeb2711666c736252303775`
and summary SHA256
`5611f85ac9d2e0d708e9d652ec426f452b8ca58122707f2639f6ed9281af3b16`
retain source11/package/assets/tools/seed closure. TLS control remains unexecuted
at this checkpoint; no full acceptance or product cause/fix is established.
Source11/gate10 remain frozen/valid.

Common16 exits1 and reaps caller35560/start3464488 with valid monitor metadata
and no monitor errors. Both application and both native prefix generations retain
original ready/stopped/browser/transfer evidence without cleanup_unknown.
The fifth, rootless/root generation `7c09bb81d59d421c80f104d616e270a8`,
starts the original API at innerPID1/start3570175 with one lifespan, available
verifier and two observed HTTP requests, then refuses HTTPS readiness:
bounded controller metadata records ValueError at native15 `probe_https:833`.
No rootless browser, canonical ready or stopped result is recorded; its original
`cleanup_unknown:true` remains. The sixth, rootless-prefixed generation never
runs. Read-only status11 log SHA256
`3643fb5ca40a9f0c6b753a969c8cfba89671b00c317d6e37572c12ea50f04b5d`
retains the failure. Rootless readiness diagnosis and required fresh all-six
acceptance remain unresolved; no product cause/fix is inferred. Source11/gate10
remain frozen/green. The completion-only all-six auditor must not run on this
failed invocation, and supplementary quiescence cannot relabel its unknown stop.

Source11 gate10 completes2026-10-21T04:49:46.332190Z with exit0 in1301.44s.
The actual `historical gate invocation (original command SHA-256 `dfe15d4ee16e8207e5ddfe1138f7416950f8e6013a5d77e8aa230bfd51dccdc4`; Git `c692d7ae4b866fefd8a743a21afdb729da0f39c4`)` run passes6475Python
(52default opt-in deselections), three locked wheel profiles,572historical frontend unit/
110mounted,2756web unit/2805combined,21sandbox/9functional metadata, two
preliminary browser and14real-API read checks. Required checks have no skips,
failures, flaky results or retries; web coverage is95.61%lines/92.83%branches.
Completed log SHA256
`fe1a0428155ab43e6154c0e8dafc8275dfac643a477973233b66ca5e16808763`
and independent `.scratch/web-005-tenth-gate-audit.json` SHA256
`7123f6932a787cb46b0477b53a261b710262822077860cd7afdcca6acb83f448`
bind the emitted reports, all1310unchanged source hashes/modes and seven exact
closed gate/API/browser identities. Docs alignment passes202human/24helpers.
This completes the source gate only: fresh common16 all-six installed
application/native/rootless acceptance and its completion audit remain pending.
Earlier failed/unknown attempts retain their original classifications.

Common16 canonical `--profile all` starts2026-10-21T04:34:23.635335Z,
exact caller35560/start3464488/UID1000, recorded in
`.scratch/web-005-common16-functional-v1.log`. Fresh manifest SHA256
`d6e91073b480b0f18f21cfe8828e94001f0e19613a79818aa277e975429af2bd`
binds native control15 `1720dac2ed5e74abfcaa8e7946d7840d88d6bfcfb139f023f1a03a44ef113b27`
and rootless control16 `d1df7a3bb8027aa90b87adb11e6850aab85f563c00b5276ecf351b686f17edb5`.
Both immutable provisioning commands exit0 and start no roles themselves;
reviewed exact producer12/13 and source11 parser55b089 are bound for this new
run. All application/native/rootless generations and the independent gate10
result are pending at this start checkpoint. No old failed result is substituted,
no acceptance is promoted, and all earlier unknowns remain preserved.

Source11 guest installation then exits0 with all1310files verified and original
bytes preserved in the fresh backup. Actual read-only foundation revalidation
also exits0: four package trees×101files, four asset trees×6members, four wheel
copies, source11 hashes/modes, probe label and preserved product3 bytes match.
Log SHA256`1d6d2371ac4b333b0d4a1e132fc9abf6c1698a1e202621d1bc78066880fd878d`;
independent host audit `.scratch/web-005-foundation4-source11-independent-audit.json`
SHA256`ed55fa5139a1ad7c758af7b6955513c08dbc7b2465eb53021b2bfc4748a7afb8`
checks exact bound source and receipt without another guest run. The new unchanged
producer12/13 sources pass52owner checks and20independent real-Unix/H11 checks;
accelerated unit cancellation is labelled supplemental, not the installed30s
proof. Gate10 and fresh all-six functional acceptance remain pending. No workload,
release or feature acceptance follows from these prerequisite checks.

Source11 freezes1310files with exactly five approved contract/parser/test changes:
inventory `.scratch/web-005-source-9v37kwww/source-inputs-v11.json` SHA256
`3358026beaad1aa0db536c1dcf41f5afdc1a20808bea556a80c41342888250f1`,
snapshot `285ca369f6a72965e0ed189f15cf3cd784ca3ddecc003228f1c81d8283906253`.
Gate10 starts2026-10-21T04:28:04.892257Z, exact hostPID2442635/start402542673,
Historical execution summary: the recorded gate included the retired interface; exact invocation and original proof remain in Git `c692d7ae4b866fefd8a743a21afdb729da0f39c4`.
`.scratch/web-005-tenth-gate-command.json`. Its exit/counts and required fresh
all-six installed execution remain pending. No passing gate or feature result
is inferred from its start.

Final parser55b08962…/test6060008b… owner run passes256/0skip
(255file+one safe-help;47unrelated help deselected), independently corroborated
by255/0skip in15.53s. Exact owner report
`.scratch/web-005-proof2-parser-FROZEN.json` SHA256
`8aeb321b670413bd71468b06e59a623d460875f6644282d4d2d3d7ef0dff31a6`
and independent XML SHA256
`988b6d960c6e3b1bf09ee93060b22efd176e45f5cf3e7f738957e144c08fd380`
retain the distinct executions; they do not replace installed acceptance.
Actual host compatibility `.scratch/web-005-source11-artifact4-compatibility.json`
SHA256`eb7e0cf8f6d578e989d0459364ed5d5405b313d1f01f68026780b45148835f7b` rechecks1310source
hashes/modes,101wheel ZIP/package members,44UI inputs and both retained build
trees. Artifact4 wheel/UI/image keep their original source10 build provenance;
this is no rebuild or relabel. Guest source11/install/package revalidation,
new protected observers and all six application/native/rootless generations
remain required. All failed common14/15 records and original unknowns remain.

Common15 exits1/reaps caller33965/start3227266 after only application/root
generation `0caa62a7b8914087abd4910cd1eb1e99`; the other five generations never
run. Both browser phases pass/drain; stopped role evidence and original generation
binding pass, while the retained result remains `cleanup_unknown`. All38 actual
accepted sockets measure8192. Three deadline probes record real CancelledError
near30.001s, incomplete131072/284996 bytes and final=false. Three cancellation
probes span2.006–2.008s and observe disconnect, but original H11 legally returns
all six ASGI awaits normally, including the final call. Those raw counters stay
unchanged; normal return does not prove protocol submission or client delivery.
Original transfer validation still refuses at line3473. Read-only diagnosis
`.scratch/web-005-common15-proof-diagnosis-v1.log` SHA256
`af9f3565000cd3bbaba68ef646f56038d6aa9cb0c85b98522a391032057c7ec6`
and observer log SHA256
`e028e5c652c6c10084a55cc6157a792a2d3683847a23bed952f5229dc1bd0bea`
preserve the actual failure; no old result is promoted.

The contract-first private transfer schema2 separates passive source-pinned
original-cycle submission/no-op states from raw ASGI and independent Node TLS/H2
zero-DATA/RST observations. It retains real deadline cancellation, incomplete
protocol submission/final=false, strict per-send exception rules and every
original drain, with no send/receive/scope/transport behavior override. Generic
network errors refuse the whole transfer. ADR147/INV013 already require actual
stalled-send/disconnect and bounded resource lifetime; no product behavior,
public wire, new dependency, invariant or ADR change follows. Only the approved
execution/testing/development documents and subsequent named runner/tests
supersede source10's freeze. All101 backend package files and44UI build inputs/
artifact4 remain unchanged. Fresh source11/gate10 and all six installed
profile/prefix generations remain required; gate9 retains its historical source10
scope. This is a proof-contract correction with implementation/acceptance pending.

Common15 canonical `--profile all` starts2026-10-21T03:54:51.413087Z,
exact caller33965/start3227266/UID1000. Manifest15 SHA256
`a7faab9d05ce56b473f9e62e42c134aba6e70fd1e59633889dcec121cd2c38b7`
binds native control14 `4e194fc49d962bc7738bea641b90b0730a1ed30fdadcde749d2f21f06607b7bf`
and rootless control15 `1059a90339d9e634cb51422dc0d620f121338c5f6d16259b8951520838db120c`;
both provisioning commands exit0 without starting roles. The owned raw AF_UNIX
control measures listener4096requested/8192effective but accepted socket212992,
explaining why the listener-only injection did not establish actual API pressure.
New fixture entrypoints10/11 measure and set each accepted socket before the
original H11 callback, retaining original ASGI send/receive and failure refusal.
Twenty-one focused checks and an independent21-check run pass without skips;
source evidence `.scratch/web-005-accepted-buffers-FROZEN.json` SHA256
`76f684bcc6faab71e31564511fdfc9a49da48dfa757e7613300b6f49eb260fd4`
retains exact sources and tests. Source10/gate9/artifact4 remain unchanged.
This records invocation start only; all six required generations, stream proof
and normal acceptance remain pending. Preserve common14's failed result and all
earlier unknowns; no case, feature or task is marked complete.

Common14 completes only the first application/root generation and exits1,
reaping caller31781/start3047342. All51trusted and3untrusted browser checks pass
with exact phase/container/init drain. Decision149's repaired foreground path
removes its own API socket; all ten original resource drains, canonical stopped
role evidence and ready/stopped generation binding pass. The later original
transfer validator refuses at `scripts/check-web-functional.py:3473`: all six
probes return their complete284996-byte body in under2ms, with final sends
complete and no incomplete/backpressured send. This does not prove the intended
client-abort or server-deadline behavior. The original failed result and
`cleanup_unknown` classification remain; the other five generations never run.
Bounded read-only diagnosis `.scratch/web-005-common14-proof-diagnosis-v2.log`
SHA256`05323846d7525cd6c33cc1b85f524d459f0abe66288ec63fe9eed25ee65715c5`
and summary `.scratch/web-005-common14-transfer-refusal-summary.json` SHA256
`8d968fdab795dc7875cab7ff7a3546cd2fd8648f86ca20ee39af6301835f7be2`
preserve the exact failed operands without weakening acceptance.
Fresh artifact4 missing-assets/wrong-manifest startup refusals independently
pass4required/4passed/0skip; postverify
`.scratch/web-005-startup-refusal-product4-postverify-v1.json` SHA256
`c9a4f631afadeea36b10d2cb3489607eb15935eb3e2acecaac13a3fb316a068b`
closes five exact identities/four cgroups and original FD/thread/task/socket/
lock/seed/101package/1310source identities. This remains a startup-refusal subset.
Source10/gate9/artifact4 stay unchanged and valid for their recorded scope. A
fresh fixture pressure diagnosis is pending; no full-feature or task acceptance
is promoted from this failed run.

Source10 ninth strict gate exits0 in1208.897s:6434Python/52default marker
deselections, all3locked wheel profiles,572historical frontend unit/110mounted,2756web unit/
2805combined, two preliminary startup and14real-API read checks. Required checks
have no skips/retries; all1310source hashes/modes remain unchanged. Log
`.scratch/web-005-ninth-strict-gate.log` SHA256
`4a7c676b896e5cc52482835cad9327dcd46bd26d5f5daa37adaca12b286ba987`;
independent `.scratch/web-005-ninth-gate-audit.json` SHA256
`9bb29e79e59031cd47ea8552fb66f848e94d5f1f28b9a29dc9735865bebf096d`.
This gate establishes source conformance, not installed shared-Caddy acceptance.
Common14 canonical `--profile all` starts2026-10-21T03:24:52.181808Z on the new
source10/artifact4 inputs, exact caller31781/start3047342/UID1000. Manifest SHA256
`3d35d0b0fbb589ab78fba4285143262589627020438a6fe8e8ec3d6df37b84f4`
binds native control13 `40d44efa…` and rootless control14 `179c4c69…`.
At this start checkpoint all six results were pending; the subsequent first-
generation refusal is recorded above, with no full case or task closure.

Source10/artifact4 checkpoint: all1310 frozen source files are installed and
verified in the owned guest, snapshot
`596943b73705ab123b6cb9191830e40a1418f491c371f554ac6f929a6f792953`.
The new445874-byte wheel
`83a3c29f23f1729f02c23d4a7aff57c2c8bd1795b3018e6c17723c80428babcd`
matches all101package sources. Two UI builds are byte-identical and equal to
artifact3, retaining manifest2ae0472d…. Artifact summary
`.scratch/web-005-artifacts-v4-2_lxvvpy/SUMMARY.json` SHA256
`3eecaaad0373a23ff43e5d86bf8b6543c56a34e79da5b9f0999a3125ff8dfc08`
and independent root review `.scratch/web-005-artifact4-root-review.json` SHA256
`fba3e0ae79b1a90605a9aa9683010b12b9bce3d7c1a09060648540843e9c097a`
bind the host builds. Gate9 was then running; no installed acceptance or functional
result is claimed. Preserve all historical source9/gate8/artifact3 evidence.

Common13 canonical all-profile execution starts2026-10-21T02:32:58UTC on
unchanged source9/product3 and exits1, with exact caller28480/start2735755 reaped.
Manifest SHA256
`7f6691de7fb7579ef049c9a3b02165a97ae8de5a4bfbd3a4cbc516f9397234a2`
binds native12/rootless13 and the instrumented browser launcher; native control12
is `953a314b10770d7e0e46f2a2040b8ff8ed494e85f4aba94823fd3bc053e6f755`.
The first application/root generation passes all51trusted checks (17per engine)
and all3untrusted checks; both browser phases and their resources drain, and the
canonical report validates. STOP produces no stopped artifact: original normal
`cleanup_unknown` remains. All measured resource/browser/control predicates pass
except the API-owned socket pathname remains present. An actual original-server control confirms default SIGTERM/Uvicorn replay exits
by signal15 after lifespan shutdown and before the owned-listener context
returns, retaining the same socket inode. Decision149 records the narrow
foreground cleanup correction before implementation. The new source regression
file passes10/10 with no skips, including actual default/repeated/custom/ignored
TERM, replacement-node preservation and activation. Fresh source gate/artifacts
and all-profile installed acceptance remain required. Independent supplemental quiescence
closes28exact identities/six cgroups and five endpoints refuse with errno111;
summary SHA256
`f99cb53b53fd6bc71e1e5ff5551a361896ad0f106213d3cb79af76de10f2b8f5`.
This does not replace normal cleanup or establish the remaining five generations,
full-feature acceptance or task completion. Earlier unknowns remain retained.
The first read-only observer `.scratch/web-005-common13-observe-v1.log` SHA256
`7a44df898235960ef169a9a38ab859a2097a091d75dd77f8eca0bb1816243916`
binds application/root generation `570449fdb26545ee91600e597d4c5d49`.
Its measured valid trusted create takes5.120370320s, exceeding the old five-second
budget without establishing the original common12 failure cause.

Fresh product3 installed startup refusals separately pass4required/4passed/0skip:
missing assets and wrong manifest, each at root and `/management`. Original
controller source SHA256 is
`6e8e09dfd83e66656f161810718cd05cc3fb6f1eb780aba9307b18d667335eec`;
execution log `.scratch/web-005-startup-refusal-product3-execution-v1.log` SHA256
`dcbd243a3c2bf2e2f80c2517d758952e8f1d1161f6bdc3e07cfc0153c4445db5`.
Independent postverification
`.scratch/web-005-startup-refusal-product3-postverify-v1.log` SHA256
`c4b4ab8e3664aed88836d93973448c7fa5cf9216ac36c0723c6f031913359e0b`
closes five exact identities/four cgroups; original FD/thread/default-executor
snapshots match, owned tasks are empty, sockets/stores are absent and the same
instance locks reacquire. All11 source/each-generation seed files,101package
files and1308source9 hashes/modes remain unchanged. This subset establishes no
shared-Caddy/browser or whole ROUTE05 acceptance. Source9/gate8/artifact3 remain historical evidence for their exact unchanged
inputs. The confirmed prerequisite correction requires fresh source/wire/build
identities, artifacts, installed proof and a complete gate before acceptance.

Common12/application canonical attempt starts2026-10-21T02:02:14UTC and exits1,
with exact caller27190/start2551610 reaped and no monitor errors. Native start
SUCCEEDS: ready-result and required protected alias sidecar exist; original
installed API/worker and real Caddy TLS pass. All fourteen installed Python MCP
SDK calls complete. It then writes browser intent and untrusted-phase proof,
but no CID/created/start record or browser report. Refusal is during/before
Podman create; no browser process or UI functional acceptance is established.
Both exact browser images and the configured init binary exist; installed docs
and the earlier passed launcher support the retained security/tmpfs options.
The original launcher discarded create stderr/exception category. A fresh
credential-free create-only diagnostic exits0 and reaps in3.72464877s with empty
stderr/no errors; its container stays stopped, with no process start or removal.
This proves the retained arguments are supported, not the original cause or a
timeout. Diagnostic source SHA256
`4284c6f823eacb6139568b37779e97c08ab00aa396f87235563a6b5ad17d6ef9`;
guest `.scratch/web005-browser-create-only-v2/SUMMARY.json` SHA256
`cfa0915ff9afb53b10069645a618ede3865ff317c3c236dfcdff6a8149980b31`.
No host log was retained for that first diagnostic execution. A new instrumented
launcher remains prerequisite work; original browser-phase and cleanup_unknown
classifications and every prior attempt remain preserved.

Independent read-only common12 postverification closes24 exact PID/start
identities, including caller27190, and four exact cgroups; API/worker Unix and
Caddy TCP endpoints all refuse with errno111. The protected alias sidecar matches
the ready API VFS inode, kernel socket inode and listener FD, Caddy's upstream
matches that same listener, and native worker FD3/file-owner981/kernel-peer0 remain
unchanged. All11 source and11 generation seed files,101 installed package files
and1308 source9 hashes/modes match. Summary
`.scratch/web-005-common12-application-postverify-summary.json` SHA256
`20084018fe8fcaed78d3d96e82cd44ede821b0a42af3036373965a482e7d0fb0`
provides supplemental absence/body/hash evidence, without promoting normal drain
or browser acceptance.

The strict alias control separately passes with both original installed listener
contexts, root/child cross-checks and exact FD baseline restoration. Overall
summary SHA256`d1fcde130661aecdf786199007f6b827c98dd22ef1c4b3708469242bfb2de7a5`;
independent postverification`1ebf4aa1…` closes root26965/child26966 and both
filesystem/kernel listener identities without signals. Collectors5/6 preserve
the original output schema and authenticate only exact retained-directory
aliases. A later actual original-worker long-path regression independently
reproduces collector6's direct109-byte connect refusal; the product worker/client
already use pinned aliases. Preserve installed-but-unrun rootless12. New
collector7 and rootless13 correct only the test probe, with46actual path-boundary/
replacement/symlink/FD regressions and90combined source checks passing;
independent review passes63checks without skips. At that earlier checkpoint native12/rootless13/common13 were uninstalled and
awaited exact bindings plus browser prerequisite diagnosis; their subsequent
installation and common13 result are recorded above. Source9/product3 and the
required green source gate remain unchanged.

A separate selected runtime audit of dirty image3 exits0 with UID/GID981,
Caps0/NNP1/Seccomp2, stock seccomp, read-only rootfs, network none and only its
public gate mounted. Actual image size287201632bytes retains the pinned
203540950-byte UBI10micro base ancestry. The original bounded probe matches101
package files, six asset files and the wire digest;35 known PATH tools and eight
known import modules are absent. Independent postverification closes four exact
recorded identities and two cgroups; the container remains stopped/retained with
exit0/PID0. Receipt SHA256
`103ba1e61d4786cfc9e0d744a770284530d80a926945ae599effed89a6480e56`;
`.scratch/web-005-ubi-image3-runtime-postverify-v1.json` SHA256
`438d315f7a05fb793271c4c5e40262d8eec5341a2bf32652afe11318d271f3b9`.
The original receipt records no root-controller identity, so this independent
check makes no absence claim for that identity. Global filesystem absence,
fresh registry attestation, clean release and full feature acceptance remain
unproved; release packaging remains WEB-021 work.

Frozen source9 eighth strict gate exits0 in1192.728s with no changed input:
6424Python/52default opt-in marker deselections; three locked wheel profiles;
572historical frontend unit/110mountedFirefox;21sandbox/9functional-driver metadata;
2756web unit/2805combined component; two preliminary startup Chromium checks
and14actual API React read checks. Coverage95.61%lines/92.83%branches/
93.02%functions; required reports contain no skipped/flaky/retried checks.
Log `.scratch/web-005-eighth-strict-gate.log` SHA256
`4747accb01ac73ac4ec1fcaa1448f990a3f32a75d25e66531a7332910b61f8a1`.
Independent `.scratch/web-005-eighth-gate-audit.json` SHA256
`3452f4087b772f6ac2d41cc38dfae3e8144a138f8b0eb36f8a67d46d2e93c05f`
rechecks all1308source hashes/modes, seven reports and seven closed identities.
The first audit refused its own atime-sensitive comparison; original log/script
remain, and corrected explicit-stable-field audit passes without changing gate
inputs or results. This source gate proves no installed functional acceptance.

Common11 canonical all-profile attempt exits1/reaps caller26620/start2416268.
Its first application/root generation`82952c411bdd4188938ab791571212a9`
positively reaches verified Caddy HTTPS REST200 and writes`network-ready.json`.
Original installed API lifespan1 and private worker PROBE pass at started,
draining and stopped; native packet denial and worker/Caddy origin probes pass.
The refusal is during helper inspection after network-ready and before
ready-result/browser/SDK compatibility. Do not call it an HTTPS failure or
browser acceptance. Four observed units are inactive/dead/Main0 with empty
cgroups; original normal cleanup_unknown remains because ready-result is absent.
Safe read-only observation `.scratch/web-005-common11-observe-v2.log` SHA256
`2e5c2a71506c6c5b127b89354736cc462f512998fd89a31c2bafb8fb788172a3`.
The first observer's source-only syntax failure remains separately retained.
Source inspection identifies a deterministic collector mismatch: original
server/worker foreground code binds through a retained directory descriptor,
while the collector requires the configured literal pathname in`/proc/net/unix`.
Its exact historical exception was discarded and is not reconstructed. A finite
owned control and strict parent-FD/socket-inode/namespace reconciliation are
being prepared; no product bind or acceptance check is weakened. Source9 and
artifact3 remain unchanged; gate8 continues independently.

Artifact3 is rebuilt and installed, retaining every earlier artifact. Wheel
SHA256`fff34031dc2e3cdc0813b075376d6c305d2fa08c1302524f832d7ecad85fac66`
contains445289bytes/101source-exact package files. Both six-file UI builds are
byte-identical, manifest
`2ae0472d0b9cdc3aa16f917c030b16b819faf05308b23592f60b96311a2805f8`;
all44build inputs match source9. Artifact evidence
`.scratch/web-005-artifacts-v3-7rq_a36n/SUMMARY.json` SHA256
`abcbb09d31b85b1c01b8ca75e93efdb9925f3816aa3cbf61e9c29e24d673562f`.
Fresh native`installed-env-v3` and user`installed-env-v11` installations each
verify101package files and wire108833…; no prior wheel/UI acceptance carries
forward. Disposable API/UI image3 is
`66cc4d3688df7ee4c2f542f9a7a637574212808efa90b746d5263297ec7256f3`,
built offline on the retained pinned UBI10micro foundation. This dirty fixture
is not a clean shipped release or proof of final contents/size.

Common11 manifest SHA256
`16e2a3ede3ad6319198a04935e11dc50feb70455e65bed6af2a0692d42e199d9`
binds all profiles to source9/wheel3/UI3/image3. Native control10 and rootless
control11 both pass immutable provisioning and101-file preflight. Independent
reviews retain nine native/70rootless source checks and eight supervisor checks;
these establish no functional result. Fresh stock-policy availability2 on actual
image3 proves AF_UNIX/AF_INET/AF_INET6 create/close, original exit0, four exact
identities gone and two empty cgroups. Receipt
`1ce1c9df4db69ba73569e02f1733b751d88ef7bb39fefce57d8024fe7016fcdc`
and independent postverification`beb70cf0…` remain prerequisite evidence only.
The ORIGINAL canonical runner starts`--profile all`2026-10-21T01:39:41UTC,
caller26620/start2416268, in guest`.scratch/web-functional-common11-v1`.
Supervisor `.scratch/web-005-start-common11-v1.py` SHA256
`49496d9ee63d34583bb5feb15e578a37149e77b38a41a5c31e4596565a479e36`
always observes a finite wait/reap after spawn, including metadata errors, and
never signals unknown children. Actual six-generation/browser/drain results
remain pending. The eighth strict source gate is independently running.

Decision148 implementation and human contracts are frozen in source9:
1308files, snapshot
`040fc0cda617de9446c035978a5babfed7ce202f72b203f7cde36b364210f901`,
inventory SHA256
`a151b4cdb5a1834722f916e5ab83c70d54e11ba296fc59ada740c82da9e2f22d`.
The owned guest verifies all files after guarded reconciliation of22 inputs,
preserving prior bytes in `p/web005-source-backup-v9`. Focused verification is
382Python/23identity/32bootstrap checks, with no required skips. Public DTOs,
routes and capabilities remain unchanged; audited wire source identity becomes
`10883335765763832f4e0aa564d5fcff1a0fcc20e41f245f16d70ce640c11be2`.
The eighth strict source gate and fresh wheel/UI builds are in progress;
installed profiles and actual shared-Caddy acceptance remain required.
Rootless10's retained source8/package2 prerequisite proves original worker/API
startup and private PROBE at started/draining/stopped. API/worker/Caddy exit0;
all seven indexed identities are gone and six exact cgroups are empty. Caller
exit1 is retained: verified HTTPS readiness refuses before any browser or
proxied API HTTP observation. No full-feature acceptance follows these facts.

Actual native9 startup isolates a prerequisite baseline compatibility defect.
The original worker runs, but original API availability refuses: the current
client requires the same configured UID for socket filesystem owner and kernel
peer. The unchanged worker requires its service-owned node while systemd's
inherited listener retains root creator credentials. Changing fixture ownership,
mode or worker validation cannot establish acceptance. Decision148 and the
standing contracts are amended before implementation: add explicit strict
`expected_socket_owner_uid`, preserving exact legacy omission behavior and all
independent checks. This is scoped prerequisite compatibility work, with no
production effects or operation replay. Source8/gate7 remain historical green
evidence; current contracts now supersede that snapshot. New source/wire pins,
assets, wheel, source gate and installed application/native/rootless evidence
are required before this task can complete.

The rootless9 startup diagnostic independently proves its original worker's20
comes from missing live NOTIFY_SOCKET. Installed Podman6.1 captures that authority
at creation, and the old fixture created outside the notifying manager. A new
immutable startup-only prerequisite moves creation into the actual Type=notify
unit, persists the bound CID before unchanged foreground attach, and retains
original ownership gates, policy and exact cleanup. It does not inject a notify
mount, substitute conmon readiness, change the worker or run browsers. Its old
source8/package2 scope cannot establish acceptance of the upcoming artifacts.

Started after clean `24625fc`, completed WEB-004, its final strict gate and
independent48-case installed-API authentication proof. Implementation authority
remains the user's kickoff; production and remote actions remain forbidden.
Decision147 records the concrete manifest/bootstrap/static-capture/stream/routing
contract before implementation. Its source proposal and independent read-only
review are retained under `.scratch/web-005-contract-draft/`; they establish no
implemented or installed conformance.

Root owns contracts/invariants/ADRs/human guides, pure URI-path encoding and
Python/command acknowledgment migration, final integration/gates/evidence.
The static owner handles protected immutable capture, configuration, application
lifespan/Boundary/routes/headers and actual adversarial/streaming tests. The wire/
frontend owner handles strict DTO authorities, audited reconstructing bindings,
deterministic build artifact/HTML markers and validated runtime bootstrap. The
independent acceptance owner implements the provider-neutral real shared-Caddy
runner, three-engine application/platform coverage and failure/cleanup proofs.
One shared work-package commit follows all required gates; collaborators do not
commit separately. Later feature cases remain pending.

Preserve the existing Caddy topology and Unix upstream, REST bearer and fourteen
read-only MCP tools, canonical raw JSON operation links/original handles/no replay,
and native Unix prefix projection. Only leading-`//` refusal and URI-encoded
Location are global prefix migrations; new origin/prefix ceilings apply only to
enabled UI. Static assets remain in the existing pinned UBI10micro API image;
there is no frontend runtime/server/image or production Caddy change. The
retained offline Caddy OCI is verified preparation, not this task's acceptance.

Owned test environments and prerequisite acquisition remain authorized. Reuse
only the newly owned guest with exact identities and independent role/network
proof, never the five unrelated historical guests. Keep failed/unknown evidence;
no source mock, TLS bypass, request interception, skipped required case or generic
network error can establish browser/Caddy acceptance. All required effects occur
only in owned disposable environments; no live NAS or production service access.

## Completion evidence

WEB-005 scoped serving/harness acceptance completes on2026-10-21, this uncommitted work package above parent24625fc. Final host source14 snapshot9257e274…8fce9/gate14 actual0 (auditd80896c6…174d4) remains distinct from installed guest source13 snapshotd3530149…e92d3/common21. Original all-profile monitor0/reaped caller60032/start5697770, six distinct normal results and independent audit283e5818…fb94d pass:306 trusted+18 untrusted actual browser checks/zero skips or retries;131 recorded PID/start pairs gone,40 cgroups empty,18 containers stopped/PID0,26 endpoints refuse. Actual metrics73321b0ce435 record17trusted+1untrusted per engine, installed Python MCP SDK14 named tools per generation, Node MCP14 named tools and two REST credential classes per engine; the old draft phrase “14 Python SDK REST calls” is superseded without rewriting historical records. Fresh bridge483ed653…156d9 proves the exact nine-prose-path13→14 delta with all1310 modes, unchanged101 package/wheel files,44 UI inputs/two builds and original source10 artifact4/image provenance. Old02acce remains unchanged with its unfulfilled common20 condition.

Actual generation/API identities: application/ e5418045eed543e4bce7fea1794bbf2d (API 82a0d473b6014adca3bef30242de6288); application/management 6b2f31567e41471aaf5ebfa0aa1d6157 (API 6ab3efbafe9747e498214cf2a3c73d32); native/ 098a9c019a5745d5bdc40703df446315 (API aa3d9bb515114777b659d5f948578a92); native/management 412ce26a52414990991ea32e89a0c084 (API 35d8701509f049dc8d3bfc5ab546bc14); rootless/ baacb01a6fa9450e8ecf573bf9465add (API 5aefe7b6db0545c99259b134c246cb05); rootless/management 3f7162b99bdc4cacb05539a5e474e8c6 (API a5d86a8216284a5aa01a2d61cb417e9f). Original record/report hashes and exact test nodes are retained in acceptance-evidence.json and the final scratch receipt. Source14 gate14 passes6643 Python/52default deselections,3 locked wheel profiles,572+110historical frontend,2756unit/2805combined web,21sandbox/9metadata,2preliminary+14real-API read checks;95.61%line/92.83%branch coverage,202human/24helper docs, no required skip/retry, all1310 source hashes/modes and seven gate processes verified. ADR147/148/149, INV013/019/021 and human API/server/security/deployment/troubleshooting guides align.

The supplemental selected-metrics v1 read-only projection refuses while decoding
SUMMARY above the helper's1MiB JSON limit; its empty output/original source remain.
Fresh v2 uses explicit16MiB bounded, duplicate-rejecting stdlib decoding and
actually exits0, receipt SHA256
`73321b0ce435f657cc2da0f911af8dab98f824055ea53c7b9f0cf1d3f638e36d`.
It reads retained records only; no workload/runtime replay or product change occurs.

Final bookkeeping verification: the focused plan/documentation/migration suite
passes78 tests (exit0), the locked documentation checker passes202 human
documents/24 helpers (exit0), and whitespace validation passes. A final
read-only comparison confirms all1310 frozen source14 hashes and modes unchanged.
The first stage-candidate audit encounters Git's aggregated untracked-directory
entry; repeating with explicit `--untracked-files=all` verifies105 scoped paths
and no unknown paths, without changing source. The full strict gate14 above
remains the source gate; only its five declared bookkeeping exclusions changed.

### Retained earlier completion checkpoint (historical)

Blocked on required application/native/rootless shared-Caddy functional
acceptance. Corrected native fixture execution and the original worker/API
startup in rootless8 remain unfinished. Separate guarded kernel/program and
stock-policy socket-availability diagnostics pass only their bounded prerequisite
scopes. Four installed startup-refusal cases pass; no full routing, browser,
stream or platform acceptance follows. Source8 gate7 passes with independent
report/process/source audit; required functional acceptance remains pending.

The retained application-v6 collector encoded a connect timeout (`errno=None`)
and success identically; it establishes neither outcome. Earlier connect-success
wording was withdrawn without altering original evidence. UID981, zero
capabilities, NNP/seccomp, configured `IPAddressDeny=any` and all five credential
open denials were positively observed; API/Caddy never started, and exact failed
start drain was independently proved. The corrected native proof must bind actual
worker/filter/control/listener evidence before original worker execution proceeds.
Do not add replacement isolation or weaken SELinux, units, policy, kernel settings
or required assertions. Owned fixture correction and diagnosis continue.

The implementation and retained preliminary evidence currently include:

- Server capture/configuration/routing/stream checks:82 focused tests and170
  preserved boundary regressions pass; the source evidence is retained in
  `.scratch/web-005-server-source-evidence.json`. These are source tests.
- Strict frontend:2756 unit/2805 combined component tests pass with95.61% line
  and92.83% branch coverage; both corrected deterministic builds produce manifest
  `a5b9e9a707a37e673591a65fc812585c159115bed6955b210e68771fdd1dcda0`.
  The44 captured build inputs still match. Preliminary Chromium refusal/fallback
  checks pass; those two checks establish no shared-Caddy acceptance.
- The corrected unpublished445074-byte source wheel has SHA256
  `0eac02b3aa56ddfbf0ccdf213a0651b0620890083fdad7095bea46b073d2eecd`.
  Both separate owned-guest installed environments match all101 package files
  and compute the actual wire digest. The disposable API/UI image is built
  from retained UBI10micro ancestry and adds image-owned root-protected assets.
  The pinned recipe introduces no additional frontend runtime; fresh runtime
  contents/tool absence/size proof remains WEB-021 work.
- The actual source MCP SDK regression invokes all fourteen original tools on
  the owned seeded archive. The distinct run/verification report IDs and seed
  immutability are checked. This regression establishes no installed Caddy or
  browser acceptance.
- Earlier owned attempts expose fixture-specific stdout labeling, a child read
  hidden by the original ProcSubset, and socket activation under an inappropriate
  `/opt` runtime path. Preserve every attempted source/generation/log. The new
  fixture uses original journal logging, controller-bound boot identity and new
  `/run` runtime paths with existing policy labels. A separate actual socket-only
  prerequisite probe passes without starting its dummy service. None of these
  corrections changes production hardening or establishes application acceptance.
  The current application-v6 attempt reaches the actual worker and fails its IP
  confinement proof prerequisite. Its ambiguous `errno=None` results must not
  be reported as actual connect success. A separate minimal diagnostic records
  two explicit two-second connection timeouts, but its controller segfaults
  before retaining live BPF queries; this partial result proves no confinement.
  Its source/log/generation and separate exact drain are preserved. A versioned
  query-only diagnostic then passes: explicit two-second TimeoutErrors, live
  direct/effective ingress and egress program IDs, no ancestor programs, and
  all12 query calls return0. Guarded256-byte storage observes kernel output at
  offsets56–63 beyond the passed32-byte prefix; do not repeat the physically
  undersized allocation or infer an unproved vendor bug/segfault cause. This
  diagnostic establishes attachment, not the programs' deny semantics or full
  worker acceptance. Independent postverification proves all14 exact controller/
  child/query identities gone, unit inactive, cgroup empty and endpoints closed:
  `.scratch/web-005-bpf-query-run-c8dca1c76bfb4d498aea84436f0314cd/POSTVERIFY.json`
  SHA256 `9c643c324595663eed2360aace9d546a2667b23e2799569b9e5402c5c9b2651f`.
  The original collector ambiguity source audit is retained in
  `.scratch/web-005-native6-outcome-source-audit.json`, SHA256
  `6024de4bb86c6044ff49bb1143e9e9de7877da3f5cdd637baaeb88448c4876fa`.
  Next proof must bind actual worker PID/cgroup/network namespace, verified
  translated deny programs before/after fresh attempts, same-UID same-namespace
  positive controls and server-side zero worker accepts. A bare timeout remains
  insufficient. No kernel/policy/isolation change is authorized by diagnosis.
  A third diagnostic uses the complete64-byte query UAPI in guarded256-byte
  storage: all12 queries return0 with no writes beyond64. Actual live ingress454
  and egress453 programs independently validate their translated8-instruction
  deny semantics; this is not a name-only assertion. Independent postverification
  proves all15 exact controller/child/query/auditor identities gone, unit inactive,
  cgroup empty and endpoints closed. Evidence
  `.scratch/web-005-bpf-query-run-5b357ecd52e246f88784c3ab899ca119/POSTVERIFY.json`
  SHA256 `57809fa14043ed48b5be44c283b7c264e98e11e9f716f0dde7a8df39fb7b709b`;
  canonical pure program recheck
  `PARENT-PROGRAM-RECHECK.json` in that directory SHA256
  `0baeb7407af400e9ee8f85bb62e3f65b83fe2d4052c206dedabdee67bfe86e4d`.
  This proves the diagnostic programs' semantics, not the actual worker's full
  same-UID/netns nonce-control and zero-accept conjunction or feature acceptance.
  Application-v6's independent failed-start audit is retained in
  `generations-v6/5830297ce9324e4e92255600afbe8538/failed-start-kernel-drain-v1.json`
  below the owned guest's `/opt/hfcache-web005`, SHA256
  `111bc2fdac0de1176824e799a177081e35ba9b27d8aae3974050387ebab9d28c`.
- Four installed native startup-refusal cases pass: missing assets and wrong
  manifest under root and `/management`, zero skipped. Actual original server
  lifespan produces typed HFCFG005/exit10 before operation state/pool/runner;
  no listener accepts. Descriptors/threads return to baseline, tasks are empty,
  socket/state remain absent and the original lock inode is reacquirable.
  Positive child exit is retained before normal unit stop, followed by exact
  inactive process/cgroup proof. Independent postverification rechecks all11
  seed files and101 installed package files for all four cases. Host evidence
  `.scratch/web-005-refusal8-postverify-evidence.json` SHA256
  `c6d16efdfdf015d484b32c75635e404074ad78d444d2d4c68ac0f17771f3c74f`;
  guest overall summary SHA256
  `4f579c5e5d78d22db52812c15dbcdfc6efa6ec906b30381eb376a157ff62d252`.
  These checks use the same corrected installed product wheel and assets but
  the retained v5 manifest; they establish only the installed native refusal
  subset, not shared-Caddy/browser or full ROUTE05 acceptance.
- The first rootless-only partial run refuses Podman's unsupported
  `create --sig-proxy=false` before any role creation. The actual pinned engine's
  help-only parser reproduction exits125. Independent queries prove all three
  intended container names absent and all three units not-found/inactive with
  MainPID0/empty cgroups. Preserve canonical `cleanup_unknown:true`, because
  missing original role proofs are not supplied by this supplemental audit.
  `.scratch/web-005-rootless-only-attempt-v1-evidence.json` SHA256
  `5ad84fa99d8fc17d6390bdaac647bdd387272cc84c69fa3eae74b6f5b121c2ee`.
  A new versioned helper removes only the unsupported create argument, retaining
  original foreground start, signal ownership and graceful stop semantics.
  The same-image/kernel stock-policy control separately creates and closes
  AF_UNIX, AF_INET and AF_INET6 sockets. Its protected receipt SHA256 is
  `d54e0152a04cca779e1a91d07978b5be8ee8620d6389944a90a5a64a848df7d0`;
  independent proof closes all4 exact process identities and2 cgroups. This is
  availability evidence only. Corrected rootless8 generation
  `c80aced9b2204132965c58e301ed394b` records actual socket-stage errno38 denial
  under the original pinned AF_UNIX-only policy, plus actual AF_UNIX socket
  create/close. Independent review verifies the retained private worker
  `proofs/final.json`: the original worker returns20, and the fixture assertion
  yields container exit1. Original API `server.run` returns without satisfying
  the required composite `server.started and observer.refs` assertion or
  producing ready proof. Neither operand was measured separately; individual
  states await the startup-only diagnostic. Caddy/browser do not start. Retain safe status metadata
  `.scratch/web-005-rootless8-runtime-status-01.log` SHA256
  `d839b17838887147602d113ae33659b28c3efdef0721dd10fb466849e537bc87`
  and bounded exception-frame metadata
  `.scratch/web-005-rootless8-log-metadata-01.log` SHA256
  `b823ae9ed632426e38bfb0d801b52ed2c7bb9578c754296e559335e25a2e13bf`.
  Worker/API startup diagnosis remains pending. Independent supplemental checks
  find all4 exact process identities gone and4 cgroups empty, but preserve the
  original `cleanup_unknown` result; this is not normal role cleanup or acceptance.
  Origin proof alone does not establish role or functional acceptance.
  Safe failed-subset summary
  `.scratch/web-005-rootless8-failure-evidence.json` SHA256
  `c11145b78974b0772093f6fd5a37d64e93076b4c34057c91176141830ee9dc92`
  preserves these measured outcomes without inferring the assertion operands.
- The first strict gate fails on two real disabled-UI route regressions, fixed
  by conditional route registration, and on superseded mixed-source wire pins.
  The second gate passes6272Python tests/52default marker deselections and all
  retained572unit/110mounted historical frontend checks, then fails web lint while the new
  functional driver is being edited. Four changed harness paths make that gate
  superseded independently of the lint result. Its1088.667-second result/log
  remain in `.scratch/web-005-second-gate-result.json` and
  `.scratch/web-005-second-strict-gate.log` (SHA256
  `5298ff4855a871fa95cb71d58910145588a5b40fb71fbe32314ad784fca101f8`).
  The third gate refuses agent execution links in a human ADR; the narrow
  correction passes the documentation checks. The fourth frozen gate passes
  6281Python/52default marker deselections, all wheel/historical frontend checks,
  2756web unit/2805combined and both preliminary browser checks, then fails the
  real-API read fixture's obsolete277-example count against297 actual examples.
  Its1171.406-second log SHA256 is
  `18e88b7bb63db7a276cdb7998f524381a9baa05b7ee1e7f6ed121ea955d7f32a`.
  The exact test-only count correction passes14/14 actual API read checks in
  both prefixes without skips/retries, with exact API/browser drain; evidence
  `.scratch/web-005-read-corpus-count-correction-evidence.json` SHA256
  `a8c6e0a98b0905c6a4bd25e0122bf78f028d6b2d4fb64fd99ac2e8b3cf4c7a5e`.
  The fifth `historical gate invocation (original command SHA-256 `dfe15d4ee16e8207e5ddfe1138f7416950f8e6013a5d77e8aa230bfd51dccdc4`; Git `c692d7ae4b866fefd8a743a21afdb729da0f39c4`)` exits0 in1173.121s
  against all1306 frozen source files, snapshot
  `bb2353cab1261936df1be140b6e20abb96a0b201e26d2e43574cf6c9ed33f5bb`,
  inventory SHA256
  `210585f49aa6797452395a0bfbd135b3ac05c7d1bf79c8dff9e9fc0470531242`.
  Result:6281Python/52default opt-in marker deselections; three locked wheel
  profiles;572historical frontend unit/110mountedFirefox;21sandbox-process/9functional-driver
  metadata checks;2756web unit/2805combined component; two preliminary startup
  Chromium checks and14real-API read checks. No required check skips/retries.
  Coverage95.61%lines/92.83%branches. Production manifest remains `a5b9e9a7…`.
  Gate log SHA256
  `8f1b750e15beb09ebf31cb440d613802dbf4d52dcf86612ba70fb1c3a637889a`.
  Independent seven-report/seven-closed-process audit rechecks all1306 source
  hashes and current200human/24helper documentation validation; evidence
  `.scratch/web-005-fifth-gate-audit.json` SHA256
  `c172b9ccd08f3fd7497133cab8774fa5e2c3a614ea5e457aa6ea13d90a189d71`.
  This green source gate establishes no shared-Caddy/native/rootless acceptance.
  Subsequent test-contract and strict execution-proof schema corrections are
  intentionally outside that frozen snapshot. The sixth gate fails six stale
  rootless fixture assertions at the new mapped-identity prerequisite, after
  6358Python passes/52default marker deselections; its retained log SHA256 is
  `30d0c3b28ff657c6b6ad61d82a31f7525ac6fdd0bb3d34e82c889467c70a5610`.
  The corrected source8 snapshot is
  `ad444c4834446cd323cffa4e42a7d0fcf4a33b07636081065f386e57a1d49b63`;
  `.scratch/web-005-source-cn5xp_vv/source-inputs-v8.json` SHA256 is
  `f7719b7358f7a8ba65d0d22cd4e9f0fe561bbfaf3842025ea7a57520f7ce0042`.
  It binds runner SHA256
  `aedfe5dc47094070ccd0db7dfebe8c84a57ea6c1dc3a18d8a4cef607df7006ca`.
  Its seventh `historical gate invocation (original command SHA-256 `dfe15d4ee16e8207e5ddfe1138f7416950f8e6013a5d77e8aa230bfd51dccdc4`; Git `c692d7ae4b866fefd8a743a21afdb729da0f39c4`)` exits0 in
  1172.025s:6401Python/52default marker deselections; all3 locked wheel profiles;
  572historical frontend unit/110mountedFirefox;21sandbox/9functional-driver metadata;
  2756web unit/2805combined component; two preliminary startup Chromium checks
  and14actual API React read checks. Coverage remains95.61%lines/92.83%branches;
  no required skipped/flaky/retried test is present. Gate log SHA256
  `2e7f769cf719922f5a48ec3e94c14195700d5a3b4e1c286f80c3ce40b2128df9`.
  Independent seven-report/seven-closed-process audit rechecks all1306source
  hashes and current200human/24helper documentation validation; evidence
  `.scratch/web-005-seventh-gate-audit.json` SHA256
  `ad63fdc900a9fbf67e2ca57c3cc4ce33ed6dd044ae59007062f05bd15277d093`.
  This source gate establishes no installed shared-Caddy/native/rootless
  acceptance. Native8 separately passes unchanged source8 canonical
  `native_origin_network` validation of its actual-worker packet/filter/control/
  listener conjunction inside the private owned guest. The original worker
  exits0, but API then fails its composite startup assertion; Caddy/browser do
  not start. Guest `p/web005-native8-network-postverify-v1/CANONICAL-RECHECK.json`
  has SHA256 `90843ff3eadf1d04e3f57e34a4c164642a0e6991b46e4ec06f2e4ea1bb9558c8`;
  host log `.scratch/web-005-native8-guest-network-audit.log` SHA256
  `31c8214d04fa2c17256038cbae0902fdf932813f2e660106b90ef4a6b14c1f1e`.
  Supplemental `.scratch/web-005-native8-network-export-v2.json` SHA256
  `ce0c67214f590d8be7d24f98169b9ffe8014f239565cb51e8441aae4ed9b4741`
  proves20 exact identities gone, four empty cgroups/MainPID0 and refused
  endpoints. Preserve original normal `cleanup_unknown`; this failed subset is
  not normal application/shared-Caddy acceptance. A host-local recheck first
  refuses the nonprivate `.scratch` directory, then the actual private guest
  recheck passes without weakening its validator or changing host modes.
  The parent monitor records actual wait/reap/refusal; startup diagnosis remains.

  Product package/build inputs remain unchanged; preserve original wheel/assets and all
  superseded/failed evidence. The stable canonical container recipe remains
  pinned UBI10micro; fresh clean release contents, tool-absence, static ownership
  and size proofs remain deferred to WEB-021, not claimed by the dirty fixture.
- Real shared-Caddy stream acceptance now explicitly requires original API
  per-send/disconnect facts from actual cancelled and zero-window HTTP2 requests
  against the built large JS member. Test-only socket pressure preserves original
  app/server/send behavior and the30-second deadline. Source-only mocked stream
  tests or an ordinary completed transfer cannot establish this acceptance.
- Source transfer refused before mutation when it found WEB-004's previously
  excluded task record. The observed bytes match both retained original source
  bundles. The next reconciliation explicitly preserves those original bytes
  before replacing the record with committed HEAD. No checkout reset or
  unexplained deletion is authorized or performed.

All95 full-feature cases remain pending in the committed ledger. On completion,
replace this section with:

- Date and exact source/artifact identities; for an uncommitted result use `WEB-005, this commit`, never a fabricated commit hash.
- Actual unit/component/integration/functional commands, exit status, relevant test node IDs, test profile/browser and safe evidence locators; explicitly separate simulated storage, isolated platform, and unperformed production/NAS acceptance.
- Acceptance-case coverage and failure-injection outcomes, required gate output, coverage/budget measurements where relevant, and zero skipped required checks.
- Human documentation created/updated and example/link validation; invariant/ADR review outcome and amendments or justified no-impact statement.
- Link to completed progress entry, operator handoff, next-task/current-selector update, and any retained limitation. A required unresolved limitation keeps this task blocked rather than completed.

## Retained selector checkpoint before source12

The following former navigation checkpoint retains its content and history;
relative Markdown link targets are adjusted from the former selector directory
to this task directory so they resolve to the same documents. This is an explicit
link-only relocation amendment, not an execution/status change. The execution
notes above own current status. Original selector SHA256 `02059fd7e7a4a4809abe8ac399a337b10fd95d41dbdb8439c728a36f309b2ea6`;
its exact494-line bytes remain in ignored
`.scratch/web-005-source12-selector-original-494-lines.md`.

~~~~markdown
# Current plan

| Field | Value |
| --- | --- |
| State | active |
| Active plan | [Web UI replacement](../2026-10-20-plan-web-ui.md) |
| Next task | [WEB-005 — Shared-Caddy UI serving](web-005-shared-caddy-spa-serving.md) |
| Blockers | Source11 gate10 passes. Common18 provisioning passes, but its unsupported rootless-only CLI attempt exits2 before workspace creation. A CapDrop metadata predicate is under read-only investigation; no new functional failure or acceptance is established. Fresh canonical all-six acceptance remains required. |
| Last completed plan | [historical frontend repair local rollout](../../history/removed-interface-records.md) |
| Updated | 2026-10-21 |

Common18 native17/rootless18 provisioning exits0 with no role/container starts.
Its attempted `--profile rootless` invocation is rejected by the unchanged
canonical CLI, whose choices are application/platform/all: caller47202/
start4002124 exits2, wait/reap observed, before workspace or role creation.
Log `.scratch/web-005-common18-rootless-functional-v1.log` SHA256
`969324ee5160c9f925b35c46a54f26de03a69537bd55c12a190fcaec5269caf7`
retains this preflight failure. A literal CapDrop metadata predicate remains an
unconfirmed fixture-validation candidate awaiting actual retained-role fields;
no runtime failure or acceptance is inferred. Fresh canonical all-six acceptance
remains required; source11/gate10 stay frozen/unchanged.

Read-only partial17v2 exits0/reaped after the retained v1 diagnostic refusal:
102 recorded PID/start identities gone,22 cgroups empty, six stopped browser
containers/PID0 and20 endpoint refusals. The three original normal generations
revalidate153 trusted/9 untrusted browser checks with zero skips; all1310 source
files, two101-file package trees,183 tools and11-file seeds remain unchanged.
Log `.scratch/web-005-common17-partial-postverify-v2.log` SHA256
`370f1d19ef88d8006ec479f6964ca39fa259b79e318fc989f7c57d02cc056d90`
retains this supplemental closure. The failed generation's missing controller
owner pair and original cleanup_unknown remain explicit. Private packet2's
strict bounded task-absence proof passes19 local checks and19 independent
checks; fresh installed acceptance remains unperformed. Source11/gate10 remain
unchanged; no old failed result is promoted.

Common18 manifest-only preparation exits0/reaped74626, retaining all1310 source
bindings. Manifest SHA256
`f2c5456f8abf315d2fe18805b10e05e4ed4120dd5a7bf72c6df7ff2a7e25d8d9`
binds fresh fixture `83d58be5-1c18-4c74-aa6c-9f24226c308b`; no role starts in
preparation. This establishes no runtime acceptance; fresh canonical all-six
acceptance remains required.

Fresh read-only failed-status projection narrows common17 to three original
normal results (both application prefixes and native/root). The fourth,
native-prefixed generation `80731eb0c80b409492721f489621288b`, fails before
API/Caddy start in private packet helper `close_listeners:656`: the second
kernel/proc task-TID absence assertion follows successful thread join and the
first no-errors/not-alive/closed-descriptor assertions. Its saved packet marker
is exactly aborted evidence, never schema2 acceptance. Observed worker status
is failed/1 with MainPID0 and empty cgroup; canonical ready/stopped/browser are
absent and original cleanup_unknown remains. Both rootless generations never
run. Projection `.scratch/web-005-common17-failed-status-v2.log` SHA256
`77ff232579de0d5ce44368104cf82ae4332b856b8cbfb6ea90a5c9c6b671005f`
retains the exact controller frames. Partial closure audit and a narrowly bounded
private-helper proposal remain pending; no product cause or accepted fix is
established. Fresh all-six acceptance is still required; source11/gate10 remain
frozen/unchanged and completion drafts remain unapplied.

Common17's actual monitor now exits1 and observes wait/reap of exact caller
42536/start3784257/UID1000. Metadata is valid, owned identity closed and monitor
error_classes empty; full acceptance is false. Completed host log
`.scratch/web-005-common17-functional-v1.log` SHA256
`e6981c14d8297b90bd1d50c136023c836de4be793da931cb83409ea681779024`
retains this failure. The final per-profile cause and cleanup evidence remain
undetermined at this checkpoint; a later read-only observer's packet-projection
schema refusal does not identify the feature failure. No SNI regression or
product cause is inferred. Completion/selector/ledger drafts remain unapplied,
and the completion-only all-six auditor remains unexecuted and ineligible for
this failed invocation. Source11/gate10/artifact4 stay frozen/unchanged;
required actual all-six acceptance remains unresolved pending read-only diagnosis.

Fresh common17 canonical `--profile all` starts2026-10-21T05:27:41.332912Z,
exact caller42536/start3784257/UID1000, recorded in
`.scratch/web-005-common17-functional-v1.log`. Manifest SHA256
`ee8a6bd314b8c946f0d4afb946d18c8fe3e460d42b6ab77d320c9452e30b979b`
binds native control16
`f302b019dcbb7415ac2e015054aed4c4a9f5396ef9fa1e39c7fdbd919c961963`
and rootless control17
`1cd57a60d9bc8fb98788678d47633a6e2b59e69dd3759c784f081b14bac8515e`.
Both immutable provisioning commands exit0/reap without starting roles.
The new rootless fixture template95ac1518…370e4 adds only fixed default SNI;
old templates/PKI/evidence remain. All six functional generations, original
monitor outcome and completion-only independent audit are pending at this start
checkpoint. Source11/gate10/artifact4 remain unchanged; no acceptance follows
from invocation or preparation, and common16's failure/unknown is not relabelled.

The isolated two-arm TLS-selection control v3 now exits0 and is independently
observed closed. Baseline records three TLSV1_ALERT_INTERNAL_ERROR failures with
no HTTP response; the sole TLS change, fixed `default_sni 127.0.0.1`, records
three strict CA/IP-verified TLS1.3 HTTP200 responses with the expected fixed
control body and the same original leaf DER. Both containers stop normally with
exit0/PID0, eight retained arm identities are gone, four cgroups empty, controller
gone and loopback33334 refused; original PKI inputs remain unchanged. Observation
`.scratch/web-005-rootless-caddy-tls-selection-v3-observation.json` SHA256
`9ee7bde543fc47d00cb5918d62b36774175586c0c625cf289ae14d2a44d8f2b0`
binds summary SHA256
`b7a2332727896d89dbad13e1a34621b6dced2156a7822dffbdb91dfe3f1066dd`.
This confirms certificate-selection behavior in the isolated fixture, with no
API/worker or feature acceptance. The minimal fixture-only template correction
is approved under the existing architecture/TLS contract; fresh immutable
common17 bindings and actual all-six acceptance remain required. Common16's
original failure/unknown and v1/v2 diagnostic refusals remain preserved;
source11/gate10/artifact4 and canonical contracts are unchanged.

TLS-selection diagnostic v2 also refuses before manager/process start or any
TLS attempt: actual Podman inspect expands `--cap-drop=ALL` into eleven named
default capabilities, while the diagnostic expects the literal list `[ALL]`.
Its sole baseline container remains retained in created state, not running/PID0;
no process/cgroup or treatment arm is started. The original diagnostic
`drained:false` classification remains. Read-only observation
`.scratch/web-005-rootless-caddy-tls-selection-v2-observation.json` SHA256
`e9281b2aa27ea6a690a1ebcb6d5f7c8334beeaee9dc6a25b655f6c51aeee48f7`
confirms the controller and six exact command identities gone after observed
waits, loopback33334 refusal and unchanged original TLS inputs. Preserve v2's
source/container/files. A fresh v3 is being prepared with the measured expanded
capability metadata plus actual live-kernel zero-capability checks; no SNI cause,
TLS positive or full acceptance is established. Source11/gate10 remain unchanged.

The isolated TLS-selection diagnostic v1 refuses before either arm starts:
its saved baseline adapter output has two actual TLS policies (explicit
SNI127.0.0.1 certificate selection plus an empty fallback), while the diagnostic
incorrectly requires one. Read-only prerequisite observation
`.scratch/web-005-rootless-caddy-tls-selection-v1-observation.json` SHA256
`240f40f030f04cb3c95d99c65471174523f1d59f396d8b6d96eb2f4272a43862`
confirms adapter exit0/observed wait, both recorded controller/adapter identities
gone, and all arm intents/CID indexes absent. Preserve installed v1 source and
partial diagnostic files; this is no TLS experiment or confirmed SNI cause.
An immutable v2 is being prepared to correct only the adapter-shape prerequisite.
Source11/gate10/artifact4 stay unchanged, and required all-six acceptance remains
unresolved.

Common16 supplementary read-only closure subsequently passes without replaying
start/stop:116recorded outer PID/start identities are gone,30cgroups empty,
11containers stopped and23owned endpoints refuse. Original canonical revalidation
passes the four normal generations'204trusted/12untrusted browser checks with
no skips. Failed rootless's three roles exit0 and API/worker resources drain,
while its original missing canonical ready/stopped/browser and cleanup_unknown
remain unchanged; the sixth generation stays unexecuted. Partial audit v1 safely
refuses because the failed CLI publishes no SUMMARY; preserved v2 reads the
five actual RESULTs without writing a synthetic summary. Its log SHA256
`ddf25132795059bcb0b96f83d108980ee8c6bfc2efeb2711666c736252303775`
and summary SHA256
`5611f85ac9d2e0d708e9d652ec426f452b8ca58122707f2639f6ed9281af3b16`
retain source11/package/assets/tools/seed closure. TLS control remains unexecuted
at this checkpoint; no full acceptance or product cause/fix is established.
Source11/gate10 remain frozen/valid.

Common16 exits1 and reaps caller35560/start3464488 with valid monitor metadata
and no monitor errors. Both application and both native prefix generations retain
original ready/stopped/browser/transfer evidence without cleanup_unknown.
The fifth, rootless/root generation `7c09bb81d59d421c80f104d616e270a8`,
starts the original API at innerPID1/start3570175 with one lifespan, available
verifier and two observed HTTP requests, then refuses HTTPS readiness:
bounded controller metadata records ValueError at native15 `probe_https:833`.
No rootless browser, canonical ready or stopped result is recorded; its original
`cleanup_unknown:true` remains. The sixth, rootless-prefixed generation never
runs. Read-only status11 log SHA256
`3643fb5ca40a9f0c6b753a969c8cfba89671b00c317d6e37572c12ea50f04b5d`
retains the failure. Rootless readiness diagnosis and required fresh all-six
acceptance remain unresolved; no product cause/fix is inferred. Source11/gate10
remain frozen/green. The completion-only all-six auditor must not run on this
failed invocation, and supplementary quiescence cannot relabel its unknown stop.

Source11 gate10 completes2026-10-21T04:49:46.332190Z with exit0 in1301.44s.
The actual `historical gate invocation (original command SHA-256 `dfe15d4ee16e8207e5ddfe1138f7416950f8e6013a5d77e8aa230bfd51dccdc4`; Git `c692d7ae4b866fefd8a743a21afdb729da0f39c4`)` run passes6475Python
(52default opt-in deselections), three locked wheel profiles,572historical frontend unit/
110mounted,2756web unit/2805combined,21sandbox/9functional metadata, two
preliminary browser and14real-API read checks. Required checks have no skips,
failures, flaky results or retries; web coverage is95.61%lines/92.83%branches.
Completed log SHA256
`fe1a0428155ab43e6154c0e8dafc8275dfac643a477973233b66ca5e16808763`
and independent `.scratch/web-005-tenth-gate-audit.json` SHA256
`7123f6932a787cb46b0477b53a261b710262822077860cd7afdcca6acb83f448`
bind the emitted reports, all1310unchanged source hashes/modes and seven exact
closed gate/API/browser identities. Docs alignment passes202human/24helpers.
This completes the source gate only: fresh common16 all-six installed
application/native/rootless acceptance and its completion audit remain pending.
Earlier failed/unknown attempts retain their original classifications.

Common16 canonical `--profile all` starts2026-10-21T04:34:23.635335Z,
exact caller35560/start3464488/UID1000, recorded in
`.scratch/web-005-common16-functional-v1.log`. Fresh manifest SHA256
`d6e91073b480b0f18f21cfe8828e94001f0e19613a79818aa277e975429af2bd`
binds native control15 `1720dac2ed5e74abfcaa8e7946d7840d88d6bfcfb139f023f1a03a44ef113b27`
and rootless control16 `d1df7a3bb8027aa90b87adb11e6850aab85f563c00b5276ecf351b686f17edb5`.
Both immutable provisioning commands exit0 and start no roles themselves;
reviewed exact producer12/13 and source11 parser55b089 are bound for this new
run. All application/native/rootless generations and the independent gate10
result are pending at this start checkpoint. No old failed result is substituted,
no acceptance is promoted, and all earlier unknowns remain preserved.

Source11 guest installation then exits0 with all1310files verified and original
bytes preserved in the fresh backup. Actual read-only foundation revalidation
also exits0: four package trees×101files, four asset trees×6members, four wheel
copies, source11 hashes/modes, probe label and preserved product3 bytes match.
Log SHA256`1d6d2371ac4b333b0d4a1e132fc9abf6c1698a1e202621d1bc78066880fd878d`;
independent host audit `.scratch/web-005-foundation4-source11-independent-audit.json`
SHA256`ed55fa5139a1ad7c758af7b6955513c08dbc7b2465eb53021b2bfc4748a7afb8`
checks exact bound source and receipt without another guest run. The new unchanged
producer12/13 sources pass52owner checks and20independent real-Unix/H11 checks;
accelerated unit cancellation is labelled supplemental, not the installed30s
proof. Gate10 and fresh all-six functional acceptance remain pending. No workload,
release or feature acceptance follows from these prerequisite checks.

Source11 freezes1310files with exactly five approved contract/parser/test changes:
inventory `.scratch/web-005-source-9v37kwww/source-inputs-v11.json` SHA256
`3358026beaad1aa0db536c1dcf41f5afdc1a20808bea556a80c41342888250f1`,
snapshot `285ca369f6a72965e0ed189f15cf3cd784ca3ddecc003228f1c81d8283906253`.
Gate10 starts2026-10-21T04:28:04.892257Z, exact hostPID2442635/start402542673,
Historical execution summary: the recorded gate included the retired interface; exact invocation and original proof remain in Git `c692d7ae4b866fefd8a743a21afdb729da0f39c4`.
`.scratch/web-005-tenth-gate-command.json`. Its exit/counts and required fresh
all-six installed execution remain pending. No passing gate or feature result
is inferred from its start.

Final parser55b08962…/test6060008b… owner run passes256/0skip
(255file+one safe-help;47unrelated help deselected), independently corroborated
by255/0skip in15.53s. Exact owner report
`.scratch/web-005-proof2-parser-FROZEN.json` SHA256
`8aeb321b670413bd71468b06e59a623d460875f6644282d4d2d3d7ef0dff31a6`
and independent XML SHA256
`988b6d960c6e3b1bf09ee93060b22efd176e45f5cf3e7f738957e144c08fd380`
retain the distinct executions; they do not replace installed acceptance.
Actual host compatibility `.scratch/web-005-source11-artifact4-compatibility.json`
SHA256`eb7e0cf8f6d578e989d0459364ed5d5405b313d1f01f68026780b45148835f7b` rechecks1310source
hashes/modes,101wheel ZIP/package members,44UI inputs and both retained build
trees. Artifact4 wheel/UI/image keep their original source10 build provenance;
this is no rebuild or relabel. Guest source11/install/package revalidation,
new protected observers and all six application/native/rootless generations
remain required. All failed common14/15 records and original unknowns remain.

Common15 exits1/reaps caller33965/start3227266 after only application/root
generation `0caa62a7b8914087abd4910cd1eb1e99`; the other five generations never
run. Both browser phases pass/drain; stopped role evidence and original generation
binding pass, while the retained result remains `cleanup_unknown`. All38 actual
accepted sockets measure8192. Three deadline probes record real CancelledError
near30.001s, incomplete131072/284996 bytes and final=false. Three cancellation
probes span2.006–2.008s and observe disconnect, but original H11 legally returns
all six ASGI awaits normally, including the final call. Those raw counters stay
unchanged; normal return does not prove protocol submission or client delivery.
Original transfer validation still refuses at line3473. Read-only diagnosis
`.scratch/web-005-common15-proof-diagnosis-v1.log` SHA256
`af9f3565000cd3bbaba68ef646f56038d6aa9cb0c85b98522a391032057c7ec6`
and observer log SHA256
`e028e5c652c6c10084a55cc6157a792a2d3683847a23bed952f5229dc1bd0bea`
preserve the actual failure; no old result is promoted.

The contract-first private transfer schema2 separates passive source-pinned
original-cycle submission/no-op states from raw ASGI and independent Node TLS/H2
zero-DATA/RST observations. It retains real deadline cancellation, incomplete
protocol submission/final=false, strict per-send exception rules and every
original drain, with no send/receive/scope/transport behavior override. Generic
network errors refuse the whole transfer. ADR147/INV013 already require actual
stalled-send/disconnect and bounded resource lifetime; no product behavior,
public wire, new dependency, invariant or ADR change follows. Only the approved
execution/testing/development documents and subsequent named runner/tests
supersede source10's freeze. All101 backend package files and44UI build inputs/
artifact4 remain unchanged. Fresh source11/gate10 and all six installed
profile/prefix generations remain required; gate9 retains its historical source10
scope. This is a proof-contract correction with implementation/acceptance pending.

Common15 canonical `--profile all` starts2026-10-21T03:54:51.413087Z,
exact caller33965/start3227266/UID1000. Manifest15 SHA256
`a7faab9d05ce56b473f9e62e42c134aba6e70fd1e59633889dcec121cd2c38b7`
binds native control14 `4e194fc49d962bc7738bea641b90b0730a1ed30fdadcde749d2f21f06607b7bf`
and rootless control15 `1059a90339d9e634cb51422dc0d620f121338c5f6d16259b8951520838db120c`;
both provisioning commands exit0 without starting roles. The owned raw AF_UNIX
control measures listener4096requested/8192effective but accepted socket212992,
explaining why the listener-only injection did not establish actual API pressure.
New fixture entrypoints10/11 measure and set each accepted socket before the
original H11 callback, retaining original ASGI send/receive and failure refusal.
Twenty-one focused checks and an independent21-check run pass without skips;
source evidence `.scratch/web-005-accepted-buffers-FROZEN.json` SHA256
`76f684bcc6faab71e31564511fdfc9a49da48dfa757e7613300b6f49eb260fd4`
retains exact sources and tests. Source10/gate9/artifact4 remain unchanged.
This records invocation start only; all six required generations, stream proof
and normal acceptance remain pending. Preserve common14's failed result and all
earlier unknowns; no case, feature or task is marked complete.

Common14 completes only the first application/root generation and exits1,
reaping caller31781/start3047342. All51trusted and3untrusted browser checks pass
with exact phase/container/init drain. Decision149's repaired foreground path
removes its own API socket; all ten original resource drains, canonical stopped
role evidence and ready/stopped generation binding pass. The later original
transfer validator refuses at `scripts/check-web-functional.py:3473`: all six
probes return their complete284996-byte body in under2ms, with final sends
complete and no incomplete/backpressured send. This does not prove the intended
client-abort or server-deadline behavior. The original failed result and
`cleanup_unknown` classification remain; the other five generations never run.
Bounded read-only diagnosis `.scratch/web-005-common14-proof-diagnosis-v2.log`
SHA256`05323846d7525cd6c33cc1b85f524d459f0abe66288ec63fe9eed25ee65715c5`
and summary `.scratch/web-005-common14-transfer-refusal-summary.json` SHA256
`8d968fdab795dc7875cab7ff7a3546cd2fd8648f86ca20ee39af6301835f7be2`
preserve the exact failed operands without weakening acceptance.
Fresh artifact4 missing-assets/wrong-manifest startup refusals independently
pass4required/4passed/0skip; postverify
`.scratch/web-005-startup-refusal-product4-postverify-v1.json` SHA256
`c9a4f631afadeea36b10d2cb3489607eb15935eb3e2acecaac13a3fb316a068b`
closes five exact identities/four cgroups and original FD/thread/task/socket/
lock/seed/101package/1310source identities. This remains a startup-refusal subset.
Source10/gate9/artifact4 stay unchanged and valid for their recorded scope. A
fresh fixture pressure diagnosis is pending; no full-feature or task acceptance
is promoted from this failed run.

Source10 ninth strict gate exits0 in1208.897s:6434Python/52default marker
deselections, all3locked wheel profiles,572historical frontend unit/110mounted,2756web unit/
2805combined, two preliminary startup and14real-API read checks. Required checks
have no skips/retries; all1310source hashes/modes remain unchanged. Log
`.scratch/web-005-ninth-strict-gate.log` SHA256
`4a7c676b896e5cc52482835cad9327dcd46bd26d5f5daa37adaca12b286ba987`;
independent `.scratch/web-005-ninth-gate-audit.json` SHA256
`9bb29e79e59031cd47ea8552fb66f848e94d5f1f28b9a29dc9735865bebf096d`.
This gate establishes source conformance, not installed shared-Caddy acceptance.
Common14 canonical `--profile all` starts2026-10-21T03:24:52.181808Z on the new
source10/artifact4 inputs, exact caller31781/start3047342/UID1000. Manifest SHA256
`3d35d0b0fbb589ab78fba4285143262589627020438a6fe8e8ec3d6df37b84f4`
binds native control13 `40d44efa…` and rootless control14 `179c4c69…`.
At this start checkpoint all six results were pending; the subsequent first-
generation refusal is recorded above, with no full case or task closure.

Source10/artifact4 checkpoint: all1310 frozen source files are installed and
verified in the owned guest, snapshot
`596943b73705ab123b6cb9191830e40a1418f491c371f554ac6f929a6f792953`.
The new445874-byte wheel
`83a3c29f23f1729f02c23d4a7aff57c2c8bd1795b3018e6c17723c80428babcd`
matches all101package sources. Two UI builds are byte-identical and equal to
artifact3, retaining manifest2ae0472d…. Artifact summary
`.scratch/web-005-artifacts-v4-2_lxvvpy/SUMMARY.json` SHA256
`3eecaaad0373a23ff43e5d86bf8b6543c56a34e79da5b9f0999a3125ff8dfc08`
and independent root review `.scratch/web-005-artifact4-root-review.json` SHA256
`fba3e0ae79b1a90605a9aa9683010b12b9bce3d7c1a09060648540843e9c097a`
bind the host builds. Gate9 was then running; no installed acceptance or functional
result is claimed. Preserve all historical source9/gate8/artifact3 evidence.

Common13 all-profile execution on frozen source9/product3 exits1/reaps exact
caller28480/start2735755. Its first application/root generation passes51trusted
and3untrusted browser checks with validated reports and browser drain. Normal
STOP remains `cleanup_unknown`: the API-owned socket pathname survives, although
supplemental evidence closes28identities/six cgroups and five endpoints refuse
(errno111; summary SHA256`f99cb53b53fd6bc71e1e5ff5551a361896ad0f106213d3cb79af76de10f2b8f5`).
An actual original-server control confirms default-SIGTERM replay after lifespan
shutdown terminates before owned-listener context cleanup. Decision149 fixes
that narrow ordering;10actual source regressions pass without skips. Fresh
artifacts and complete installed acceptance remain pending. Fresh product3
missing-assets/wrong-manifest startup checks pass4/4 with
zero skips, with five exact identities/four cgroups closed and original FD/thread/
lock/seed/package/source closure independently verified (postverify log SHA256
`c4b4ab8e3664aed88836d93973448c7fa5cf9216ac36c0723c6f031913359e0b`).
Source9/gate8/artifact3 remain historical evidence for their exact inputs. The
confirmed prerequisite needs fresh source/wire/build identities and artifacts,
a new complete gate and application/native/rootless acceptance; earlier unknowns stay.

Decision148's prerequisite native compatibility amendment preserves exact legacy
defaults and independent inode/mode/peer/worker checks. Its 382 focused Python
tests pass. Frozen source9 contains1308files, snapshot
`040fc0cda617de9446c035978a5babfed7ce202f72b203f7cde36b364210f901`;
the owned guest verifies every file after preserving22 replaced/new inputs.
The eighth required source gate exits0 in1192.728s:6424Python/52default
deselections, three locked wheel profiles, retained572/110historical frontend,2756web unit/
2805combined, two preliminary startup and14actual API read checks. Independent
seven-report/seven-closed-process audit rechecks all1308hashes/modes, with no
required skipped/flaky/retried check. Artifact3's445289-byte wheel matches
all101package files; two UI builds are byte-identical with manifest
`2ae0472d0b9cdc3aa16f917c030b16b819faf05308b23592f60b96311a2805f8`.
Both fresh installed environments compute the new audited wire digest; disposable
API/UI image3 remains on the retained pinned UBI10micro foundation. Common11
manifest`16e2a3ed…` binds all three profiles to source9/wheel3/UI3/image3.
Both protected role controls pass provisioning without starting services; the
original canonical `--profile all` run starts2026-10-21T01:39:41UTC in the owned
guest, then exits1/reaps its exact caller. First application/root reaches real
Caddy verified HTTPS REST200 and writes network-ready; original API lifespan1
and worker PROBE pass at started/draining/stopped. Inspection refuses before
ready-result/browser. Read-only evidence observes four inactive units/Main0 and
empty cgroups; preserve original cleanup_unknown. Collector literal-path checks
conflict with original retained-directory-FD bind spelling. Strict actual
inode/FD/namespace reconciliation is being tested without changing product binds
or acceptance requirements. Source8/gate7
and package2/assets2 remain historical evidence.
Common12/application subsequently reaches ready-result, strict Unix alias
reconciliation, verified Caddy TLS and all fourteen installed Python MCP SDK
calls, then refuses before any browser/CID is established. A fresh create-only
diagnostic exits0/reaps in3.72464877s with empty stderr and no process start;
this establishes supported arguments, while the original cause remains unknown.
Independent postverification closes24 exact identities/four cgroups and confirms
endpoint refusal, alias/ready-body linkage,11 seed files,101 package files and
all1308 source9 hashes/modes (summary SHA256
`20084018fe8fcaed78d3d96e82cd44ede821b0a42af3036373965a482e7d0fb0`).
Original cleanup_unknown/browser-phase uncertainty remain. New rootless13's
fixture-only pinned-parent probe passes90 combined/63 independent checks;
native12/rootless13/common13 were then uninstalled and awaited bindings and
browser diagnosis; the later installed common13 outcome is recorded above. The eighth source gate remains green; functional acceptance is pending.

The separate dirty image3 runtime audit exits0 and independently matches101
package/six asset files and the wire digest under UID981, Caps0/NNP1/Seccomp2,
read-only rootfs and network none. Its35 selected PATH tools/eight import modules
are absent; four recorded identities and two cgroups close. The287201632-byte
image retains its pinned203540950-byte UBI10micro base ancestry. This selected
runtime proof establishes no global filesystem absence, fresh registry or clean
release acceptance; WEB-021 remains pending.

Rootless10's old-source prerequisite now proves original worker/API startup,
original private PROBE and normal exits of API/worker/Caddy. All seven indexed
identities are gone and six exact cgroups empty. Its caller still exits1 at
HTTPS readiness, before browser invocation; do not count it as acceptance.

The explicit implementation instruction activates the extracted web UI plan on
`feat/web-ui`. HEAD matched its reviewed baseline `6b8fae2` exactly; the prior
selector was inactive. The bundle is intended new planning material. No older
plan or historical backlog is activated or abandoned.

WEB-001 completed the contract/ADR/acceptance/prerequisite audit and fixed a
reproduced baseline Bash frame-reader wait defect. Its corrected strict gate
passes 5308 Python/572 historical frontend unit/110 mounted Firefox tests. All 95 web feature
cases remain pending. The exact original baseline and failed evidence remain.

WEB-002 adds the strict React workspace, required web gate, full locked license
inventory, retained per-run evidence and actual preliminary browser checks. Its
final strict gate passes 5337 Python, 572 historical frontend unit, 110 mounted Firefox,
45 web unit/50 combined component and 2 sandboxed Chromium tests. Coverage is
98.46% lines/98% branches. The source preview is disconnected; Caddy/API serving
and authentication remain unimplemented. All 95 feature cases remain pending.
An extra whitespace check found a generator-added trailing notice separator
after the unpublished commit. Its narrow correction passes the complete strict
gate again; that same work-package commit is amended before advancing.

WEB-003 completes authoritative route/mode projections, generated reconstructing
decoders, bounded exact numeric/Unicode validation and a same-origin client.
Its strict gate passes 5452 Python, retained 572/110 historical frontend, 2718 web unit/2744
combined component, two shell and 14 real-API React browser tests with no required
skip. Coverage is 95.85% lines/92.94% branches. This read fixture remains temporary
until WEB-005 and proves no Caddy/Basic/installed behavior. All 95 feature cases
remain pending. Next is WEB-004; known baseline prefix/header issues are recorded
for WEB-005's routing acceptance.

WEB-004 completes the protected optional Basic provider, internal permissions,
exact-subject key namespace, bounded off-loop verification and CSRF. A fresh owned
CentOS guest proves48native browser checks through real installed API TLS in three
engines/both prefixes, including actual OPTIONS refusal and exact cleanup. Final
strict gate exits0:5940Python/52default deselections,572/110historical frontend,21process,
2722unit/2748combined web and2shell/14real-API read checks; all1278source hashes
match the guest. Earlier failures remain. Decision146 and human/standing contracts
align. All95full feature cases still await required layers. Next is WEB-005's
authenticated static serving, bootstrap and actual shared-Caddy harness. No
production deployment or installed native/rootless application-role proof follows.

WEB-005 remains blocked on required application/native/rootless shared-Caddy
acceptance after clean `24625fc`. Owned prerequisite diagnosis and fixture
corrections continue without changing product hardening.
Decision147 fixes bounded immutable
capture, strict bootstrap/build identity, Basic-only UI serving and exact routing/
header/prefix contracts before implementation. The shared-Caddy functional harness
must use actual built assets, installed API over Unix and trusted test TLS in all
three engines, preserving concurrent REST/MCP and owned native/rootless boundaries.
No WEB-005 acceptance is claimed by the preceding direct-TLS authentication run.
The earlier frozen1306-file source snapshot is `bb2353ca…`; its fifth required
source gate passes in1173.121s with6281Python, retained572/110historical frontend,
2756web unit/2805combined, two shell and14real-API read checks. An independent
seven-report/process audit confirms unchanged source and exact local drain.
Subsequent execution-proof schema/test-contract corrections supersede that
snapshot; product wheel/assets are unchanged. The sixth gate fails six stale
fixture assertions after6358Python passes. Corrected source8 snapshot
`ad444c4834446cd323cffa4e42a7d0fcf4a33b07636081065f386e57a1d49b63`
and runner `aedfe5dc…` pass gate7 in1172.025s:6401Python/52default deselections,
retained572/110historical frontend,2756web unit/2805combined, two preliminary startup and
14real-API read checks. Independent seven-report/seven-closed-process audit
rechecks all1306source hashes; required checks have no skips/retries. This source
gate establishes no installed shared-Caddy/native/rootless acceptance.
The fourth gate's final real-API
read fixture expected an obsolete corpus count; the exact correction independently
passes14/14 checks. All four actual installed missing-assets/wrong-manifest
startup-refusal cases pass with independent process/cgroup/socket/lock/seed and
101-package-file postverification. This subset proves no Caddy/browser acceptance.
Guarded64-byte-UAPI query3 proves actual attached program semantics in its
separate diagnostic unit, with all15 exact processes and endpoints drained;
it proves no actual worker/shared-Caddy acceptance. A same-image/kernel stock
policy control separately proves socket-family availability. Rootless8 then
records policy-bound socket-stage errno38 denials and a real AF_UNIX positive,
but the original worker returns20 (the fixture assertion yields container exit1)
and API returns without its required composite startup assertion/ready proof;
its individual startup states remain unmeasured. Caddy/browser do not start.
Native8 separately passes unchanged canonical validation of its actual-worker
packet-filter conjunction, then fails the API composite startup assertion before
Caddy/browser. Supplemental proof closes20 exact identities/four cgroups and
confirms original worker exit0; original normal `cleanup_unknown` remains.
Startup diagnostics and required shared-Caddy functional acceptance continue.
Independent supplemental
PID/cgroup absence does not replace the original cleanup_unknown result. Preserve
all earlier ambiguous/refused attempts and their evidence.
The canonical service recipe remains pinned UBI10micro. Fresh release runtime
contents, tool absence, static ownership and size proof remain WEB-021 work.

Scope permits source changes and owned local/disposable tests only. No merge,
push, tag, production deployment/Caddy reload, service/timer/credential/guard
change, NAS access or installed predecessor interface uninstall. Preserve the earlier operator
handoff and all original candidates, backups, locks, stores and handles.
~~~~
