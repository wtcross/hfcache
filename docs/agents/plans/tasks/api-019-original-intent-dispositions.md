# API-019: Bounded durable rejection/fencing and authenticated reconciliation

| Field | Value |
| --- | --- |
| Status | completed |
| Plan | [Job recovery and archive writes](../2026-11-03-plan-job-recovery-and-archive-writes.md) |
| Depends on | WEB-031 |
| Execution | `gpt-6.1-sol` / `high`; explicit task-agent setting required |

## Scope and acceptance

Bounded durable rejection/fencing and authenticated reconciliation; preserved admitted jobs, Basic namespaces and unknown historical outcomes, with focused race/crash/authorization tests.

The parent plan's applicable scope, acceptance criteria and safety prerequisites
are binding. No remote pushes, image publication, release tags, automatic
schedules, unrelated permissions, archive initialization, manual archive writes,
reboots, NFS disconnection or other-host effects are authorized.

## Contracts, invariants, and ADRs

Reviewed INV013/014/023, FS02/19/21–23, AD16/17 and ADR114/115/118/145/146/150/154/164.
The existing namespace digest preimages, public receipts/problems/results,
archive identity, original locks and protected outcomes remain unchanged.
ADR164/schema13.3/protocol and INV023 now explicitly allow one monotonic
refusal-review enrichment while retaining every original refusal field. A
later denied transmission cannot prove earlier missing-history nonexecution.
No new architectural family or runtime dependency is introduced.

## Validation

| Changed requirement | Smallest meaningful check | Observed result |
| --- | --- | --- |
| Permanent bounded dispositions and unchanged namespaces | Focused store validation, quota, receipt precedence, cross-process race and crash injection tests | Pass: focused7/8/12 and strict gate25 |
| Own-key GET, fresh refusal hint, strict authorization and degraded exact-ID reads | Focused ASGI tests with authenticated subjects and failed durable writes | Pass: focused7/8/12 and strict gate25 |
| Shared admission/execution and exclusive review interlock | Independent-description queue/worker lease and timeout/race tests | Pass: focused7/8/12 and strict gate25 |
| Worker/helper actual executor and pending-effect proof | Focused private worker/helper protocol and refusal tests | Pass: focused7/8/12 and strict gate25 |
| Offline activation and predecessor compatibility | Owned installer fixtures plus actual c23abba reader drill | Pass: focused7/8/12 and strict gate25 |
| Readiness bounded helper evidence | Focused nullable/grant/authentication checks | Pass: focused7/8/12 and strict gate25 |
| Complete package | `rtk proxy scripts/check.sh --require-web` | Pass: focused7/8/12 and strict gate25 |

Required gate is strict because audited source provenance changed. Generated
web changes only refresh the source digest/header; new browser decoders and
controller behavior belong to the next browser task.

No optional instrumented functional runner or new validation collector is authorized.
Raw failures are retained; the required gate froze all1276 source files unchanged.

## Execution notes and handoff

Activated 2026-11-03 by the user's explicit end-to-end implementation instruction.
Protected deployment, controlled writable transition, selected Sync and refresh
pilots and bounded metadata backfill are authorized after the reviewed safety
prerequisites. Scope is this host/current boot with fail-closed manual startup
permitted; unattended boot acceptance remains separate.

## Completion evidence

Strict gate25 passes `rtk proxy scripts/check.sh --require-web`:9644 backend
checks, three locked wheel profiles,3757 web unit/4115 combined component checks,
11 built Chromium checks, actual Library zoom and the real HTTP/API React read
fixture. Elapsed1594.475s; all1276 source names/hashes remain unchanged. Inner
log SHA-256 `ab10e6eb539e8a9403890bd60163547283a996fa94195c26ab41dbd179cb4e2c`;
shadow `8f917bc58e6b56446e3f1585592732d982de9db078a7e529d6e4c3c522227351`.
Completion records written afterward pass 69 focused documentation checks and
documentation alignment; they are not claimed inside that frozen manifest. WEB-032 is selected next.

Source-focused run7 passes908 tests in54.04s (log8ede6fa3); run8 passes74
targeted tests in18.44s. After concrete publication/deadline/query-order review,
run12 passes388 affected tests in69.48s. Lint/types/documentation alignment
pass. Raw attempts and exact source manifests remain under
`.scratch/api019-validation/`; failures and failed temp fixtures are preserved.

The first strict gate is deliberately stopped after backend failures: malformed
request tests counted the new required empty marker as a receipt. Assertions now
require exactly that marker and zero entries, preserving zero receipt/fence
guarantees. Other updated predecessor expectations require a distinct key after
durable refusal, permit bounded concurrent fresh checks outside locks while
retaining exact single admission/execution assertions, and explicitly provision
spawned-process fixture state before concurrent opening.

Owned real fsync failure after receipt rename now classifies only the publisher's
exact un-enqueued receipt under the original flock/admission lease, returns
uncertainty without202/closed hint, and refuses acknowledgement of known phantom
active state. Duplicate closures confirm directory durability before returning.
An absolute review deadline bounds private frame reads across trickled chunks.
Unsupported query/body/key inputs cannot publish fences. Actual c23abba source
reader execution refuses empty/populated marker scans and post-expiration scans,
while compatible exact-ID receipt/result reads remain available.

A narrow real worker-entrypoint reproducer exposed missing explicit companion
provisioning in the native/PID1 test fixtures. Only fixture setup changed;
listener, inherited-descriptor and offline assertions remain. Run16 passes85
affected worker-bootstrap/archive-init/API-intent tests in44.74s with no coverage
output overlap. Read-only storage retains the original HFMNT004 taxonomy without
claiming durable rejection when disposition persistence is unavailable.

Strict gate17 stopped gracefully with7150 passes and11 failures; all raw evidence
is preserved. Selected-policy UUID activation, actual unactivated factory imports,
fixed-lane pre-probe validation, and exact three-route contract/security inventories
resolve those failures. Generic Job duplicates preserve their original202/ID;
fixed protected configuration/host-effect POST authorization and independent
outcome rules remain unchanged. Metadata charges now include bounded intent
lookup/fence work while denied domain/executor calls remain forbidden. Focus19
passes175 affected tests in37.07s; no coverage artifacts overlap the strict gate.

Gate20 preserved two MCP inventory failures when the new advisory readiness
read met the existing fixture's unconditional forbidden helper. Exact repro21
confirms that cause. The existing MCP inventory now permits only readiness
status observation through the existing bounded status fixture, asserts nullable
bearer grants and retains every other helper prohibition and real command check.
Focus22 passes all5 MCP acceptance tests in6.05s. The graceful gate interruption
landed in pytest fixture setup and its own teardown raised a stash KeyError;
its failed raw log and full temporary payload remain preserved.

Gate23 reaches the normal complete backend summary:9634 pass/10 fail. Six
isolated signal fixtures used an unavailable test-module import; the resulting
unclosed child pipes caused deferred warnings in otherwise successful storage
and prune tests. The signal child now uses actual product imports with explicit
owned parent activation and exact-child pipe closure. Two UI startup-order
checks retain the actual unactivated factory so captured-root/store failures
remain exercised. Focus24 passes all267 signal/storage/synchronize/UI tests;
no storage/prune assertion or product behavior changed.

Capacity retirement uses only reviewed exact current-task temporary roots after
complete source/archive inventories and fresh all-UID no-owner proofs. Full
failed payloads, original manifest bytes/hashes and raw failed logs remain in
verified compressed archives; redundant manifest sidecars compress losslessly.
Gate23's complete archive is retained at
`/var/tmp/hfcache-api019-gate23-retirement-evidence/temporary-tree.tar.gz`
(SHA79224a97), with durable relocation/return receipts813e727a/8ae9e0a9; the
temporary HOME copy was removed only after verifying/fsyncing that exact return
copy. No historical cleanup, cache deletion, production mutation or gate-threshold
reduction occurred. Successful gate25 TMP alone retires after its complete
164266-entry manifest459b1289 and fresh no-owner recheck, receipt3eeb110c; all
source/browser/log evidence remains. Post-retirement root free1060589568B and
home48721920B require capacity planning for the next full gate.

Source/owned fixtures do not establish installed acceptance.
OPS-027 still owns the fixed selected-image offline activation invocation,
native/rootless original/companion binds, provisioning/label and actual previous-
executor drain; WEB-033 owns installed profile proof. WEB-032 owns closed frontend
DTO/decoder/route entries, causal saved not-admitted restoration, monotonic
review-enrichment projection and visible GET-only recovery. Installed helper/executor
confinement, deployed retirement and archive writes remain later acceptance.
