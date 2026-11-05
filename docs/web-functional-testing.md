# Web functional test reference

This reference is for contributors running the optional instrumented shared-Caddy
fixture. Start ordinary development with [development](development.md); use the
[deployment guide](web-ui/deployment.md) for installation. Fixture evidence is
private test metadata, not an API or durable application format.

The source gate is `scripts/check.sh --require-web --with-build`. Direct installed
workflow acceptance is separate: exercise real browsers through trusted Caddy,
the installed application, private worker and helper on supported native/rootless
profiles at root and `/management`. Deterministic Hub/storage fixtures must remain
labelled; they do not prove real NFS or installed confinement. Preserve failures
and original operation handles. Never replay an accepted or uncertain effect to
replace missing observation.

## Optional runner and evidence ownership

The [runner](../scripts/check-web-functional.py) is optional diagnostic tooling.
Its `--help` performs no runtime or credential inspection. Explicit
`scripts/check.sh --require-web --with-build --with-web-functional` requires its
complete application and platform profiles and final case selection. Missing
prerequisites or skipped checks fail; direct workflow evidence cannot be reported
as a passing invocation of this runner.

The runner's `--require-through` values retain historical coverage-group IDs for
selection compatibility. They are fixture selectors, not a task queue. The final
selection covers all 95 scenarios; required minimum test layers still apply.
Product workflow acceptance does not require every scenario in every matrix cell.
The optional instrumented runner retains its stricter complete-cell validation.

Local `--profile application|native|rootless` selects one of the three manifest
profile keys. Common source, indexed wheel, UI and toolchain identities must
match. Only selected live bindings are inspected. Rootless also requires
root-owned immutable unselected `installed.tooling={prefix,python:{path,sha256}}`,
actual interpreter/import validation and complete same-indexed-wheel verification.
This SDK does not replace container, actor or selected-image evidence. Run on
explicitly owned boot-bound guests without mixing selected-release layouts.

One fresh lowercase 32-hex `--run-id` binds the three invocations. Before role
admission, persist exclusive fsynced schema-1 `RUN-INTENT.json` with run ID,
profile, fixture ID, guest identity/boot ID, manifest path/digest and original
workspace. Runtime/browser reports, role RESULT and SUMMARY repeat that ID;
SUMMARY retains the intent and original context. Use a fresh fixture for every
profile/prefix/browser combination: 18 paired ready/stopped lifecycles across
Chromium, Firefox and WebKit. Preserve fixed-helper identity within each pair and
previous state when preparing the next. The existing 45-second callback,
navigation, locator and launcher budgets remain finite.

Join exactly three fresh normal SUMMARYs with `--profile all --run-id ID
--manifest ABSOLUTE_PROTECTED_JSON --join-summary PATH SHA256` (one summary
argument for each profile) and a required selection (`--final`, or the supported
`--require-through` selector). Offline joining validates common source/indexed
wheel/UI/toolchain bytes. Original profile manifests, intents and proofs retain
guest, boot and selected-role authority; offline joining does not perform live
wrong-host, selected-native, account or rootless checks. Common test sources and
toolchain snapshots must match; profile-specific identities remain distinct.

Retain bounded public proof copies in each workspace alongside original metadata.
The offline resolver strips only the exact original workspace prefix into the
supplied SUMMARY parent. Reject outside-workspace imports, symlink ancestry,
`..`, arbitrary rewriting and absent or hash-mismatched bytes. Copied inode,
device and timestamp facts are historical observations, never remote
re-observation. Finalization performs no remote, credential, selector or network
work. Recompute acceptance executions and case summaries; reject one-off status
stamps, retries, duplicate/missing generations or cells, unknown drains and
pending assertions. The final instrumented matrix remains 95 cases × 18 cells.

## Fixture isolation

Use owned synthetic manifests and tiny ordinary-file trees through the existing
fake-Hub and mount-table seams. Actual HTTP must reach production routes/services.
Verify installed module bytes against the selected wheel. Root-capable tests run
only in owned isolated guests; no production managers, archive, control stores,
rootful/privileged fallback or global security-policy edits are test surfaces.
Production initialization is never a test setup step. A real NFS fixture requires
a separately authorized disposable export and its own archive identity.

Generate test credentials and private PKI in restricted workspaces. Trust the
fixture CA explicitly: TLS bypass flags, wildcard hosts and permissive CORS do
not prove authentication. Pin build inputs separately; runtime/gates never pull
images automatically. Inspect actual peers/processes, bind visibility, worker
IP/credential denial, Caddy isolation, API identity and UI secret absence.
Cleanup acts only on positively identified owned resources after confirmed exit;
failed drains retain evidence. Do not log credentials, Authorization headers,
response bodies or production data in traces.

## Static streaming execution-proof schema2

This private fixture format uses exact integer `schema_version: 2`. Preserve
failed schema-1 reports and original counters without retrospective conversion. A normal ASGI `send` await return records
an application-call outcome. It establishes neither original protocol submission
nor client delivery: the pinned original H11 implementation can return normally
without writing after disconnect. Do not fabricate an error, change application
behavior, or rename that normal return to obtain a passing test.

The existing private JSONL file remains bounded to256 rows/1MiB; exactly six
original Node request UUIDs join cancel/deadline probes in Chromium, Firefox and
WebKit. Retain exact fixture/generation, original API instance/core-object
identity, trusted phase/native Basic, selected indexed member/path/length and
independent Node TLS/HTTP2 zero-window/zero-DATA/RST/session-close evidence.
Concurrent bearer observations, zero before/after stream/task inventories and all
original API/worker/listener/process/browser/container drains remain mandatory.
No debug endpoint, submitted header, credential or response body is logged.

The closed row retains these original fields and meanings:
`schema_version`, `fixture_id`, `generation_id`, `phase`, `engine`, `actor`,
`request_id`, `instance_id`, `object_ids`, `method`, `path`, `status`,
`selected_body_bytes`, `started_ns`, `finished_ns`, `body_send_started`,
`body_send_completed`, `body_bytes_started`, `body_bytes_completed`,
`final_send_started`, `final_send_completed`, `disconnect_received`,
`disconnect_ns`, `error_kind`, `streams_before`, `streams_after`, `body_sends`.
Add exactly `protocol`, `protocol_body_send_submitted`,
`protocol_body_bytes_submitted`, `protocol_final_send_submitted`. The first two
submitted counters are nonnegative integers; the final flag is a boolean.
`body_send_completed`/`body_bytes_completed` still count ASGI await calls that
return normally, including disconnected no-ops. `final_send_completed` still
records the final ASGI call's normal return. `error_kind` preserves the actual
exception classification, including null when no exception occurs. Booleans are
never integers; unknown/missing fields and inconsistent counters refuse.

`body_sends` stays bounded to130 entries. Each entry retains exactly
`sequence`, `bytes`, `more_body`, `started_ns`, `finished_ns`, `error_kind`, and
adds exactly `protocol_before`, `protocol_after`, `protocol_result`. The result
enum is `submitted|disconnected_noop|raised`, independently derived below.

### Original protocol binding

`protocol` has exactly `identity`, `cycle_id`, `scope_id`, `protocol_id`,
`transport_id`, `send`, `protocol_class`, `socket`. IDs are positive integers
from the actual objects, cached for one original ASGI invocation; they are not
user tokens or a promise of unique IDs across garbage-collected requests.
`identity` has exactly `pid` and `start_ticks` and equals the original API ready
proof's **inner** identity: PID is an integer>=1 and start ticks a canonical
positive decimal string. A rootless API PID1 is valid; independent original
host PID/start, namespace and UID/GID mapping checks still apply, with host
process PIDs>1. Never interpret an inner PID as a host PID.

`send` has exactly `module`, `qualname`, `source_sha256`, fixed to
`uvicorn.protocols.http.h11_impl`, `RequestResponseCycle.send`, and
`a3154a6c2cfaaaebe19ac7aa255dfe9b6b7b490de1da95274c033aa093e8c322`.
`protocol_class` has those same three keys, fixed to `__main__`,
`install_accepted_buffer_pressure.<locals>.AcceptedBufferProtocol`, and the
exact protected installed entrypoint's lower-case SHA256. Its digest must agree
across all six rows and the independently read accepted-buffer sidecar.
`socket` has exactly `descriptor`, `device`, `kernel_inode`, `family`, `type`,
`send_buffer`: descriptor/device are nonnegative integers, kernel inode positive,
family `unix`, type `stream`, and actual send buffer exactly8192.

Before invoking the unchanged original application, prove incoming `send` is
bound to the exact original `RequestResponseCycle.send` function and exact cycle
type. The cycle's scope is the identical incoming GET scope. Cache the actual
cycle, its exact flow object and transport. The transport's actual protocol is
the installed accepted-buffer protocol, whose cycle/scope/transport are those
same objects. The class inherits original H11 behavior except the existing
accepted-socket `connection_made` measurement. Prove a live actual
AF_UNIX/SOCK_STREAM FD, stable fstat kernel identity and effective SO_SNDBUF8192.
The original startup wrapper passes arguments unchanged and proxy headers stay
disabled. Unknown wrappers or a changed binding refuse; do not search arbitrary
closures for a nearby cycle.

The existing separate `accepted-buffers.jsonl` sidecar must independently join
that socket device/inode/descriptor, API identity and class digest. Protected
helper/role source records and actual sidecar bytes remain required audit
inputs; a transfer row is not its own independent audit. After connection loss,
the FD may be-1 and transport protocol null. Use cached proven identities; never
reopen a reused FD. A non-null protocol must still be the cached protocol.
Cycle/flow/transport object identity must remain unchanged before and after every
call, including exceptional returns and pipelining.

No application, send, receive, transport-write, message, scope or response-body
behavior override is allowed. This proof adds passive observations around the
original await only; the original accepted-socket pressure fixture remains.

### Snapshots and independent derivation

Each before/after snapshot has exactly `cycle_id`, `transport_id`, `disconnected`,
`response_started`, `response_complete`, `write_paused`, `transport_closing`,
`write_buffer_bytes`. IDs equal the initial binding. Flags are exact booleans
read from the cached original cycle/flow/transport; buffer bytes is an integer
0..1048576. Read before immediately before the unchanged await and after its
normal return or in its original exception handler. Add no await, blocking I/O,
drain, cancellation or event between snapshots and that call. Existing monotonic
timestamps bracket the call. For body calls, headers have already made original
`response_started` true and it must stay true; `response_complete` starts false.
Any completed protocol response refuses a required incomplete-response proof.

Derive every result and counter independently from the raw observations:

- An actual exception yields `raised` and no successful submission for that call.
  **Any** raised call accepted within the required proof must be an actual
  CancelledError at a paused, non-disconnected, started/incomplete original-flow
  await. Generic OSError, send_error, timeout or other exceptions anywhere make
  the whole transfer unknown/refused, even if another send has a good witness.
  An exception after possible write submission is unknown, not accepted proof.
- A normal return with `after.disconnected=true` yields `disconnected_noop`,
  incomplete response and no submission. A false-to-true disconnect transition
  requires `before.write_paused=true`: the pinned original method has only its
  initial flow-drain await and no await between its disconnected test, write and
  return. An already-disconnected instant no-op proves no timed backpressure.
- A normal return with `after.disconnected=false` yields `submitted`; before
  must also be non-disconnected. For this original GET body path the pinned
  method reaches its encoder/transport-write branch synchronously. This is
  protocol/transport API submission, never client receipt or durable delivery.

Submitted send count is the number of `submitted` entries; submitted bytes is
exactly their byte sum; submitted final is whether any has `more_body=false`.
Raw ASGI completion counters instead continue to count actual normal returns,
including no-ops. A protocol response cannot become complete then incomplete;
any true completion state refuses the required proof.
Within the same cached cycle, `disconnected` never changes true-to-false,
including between a preceding after-snapshot and the next before-snapshot.

### Required interruption conjunctions

Cancellation retains the original Node cancel/RST, zero DATA, UUID, actual
`http.disconnect`, request duration1.5..10s and exact stream/task release. At
least one same-cycle original await must last>=1.5s, begin started/incomplete,
paused and non-disconnected, then end disconnected/incomplete. It must either
return normally as `disconnected_noop` with null error, or raise the actual
CancelledError. Subsequent instant no-ops alone are insufficient.

Deadline retains the original Node hold>=35s with no client cancellation before
the original30s API deadline, zero DATA, UUID, request duration29..36s and exact
stream/task release. Require actual CancelledError raised by an original send
that begins paused/non-disconnected/started/incomplete; its await lasts>=29s
and the response remains incomplete. A normal no-op or long generic network
failure cannot prove the deadline.

Both cases require `0 <= protocol_body_bytes_submitted < selected_body_bytes`
and `protocol_final_send_submitted=false`; a fully submitted/completed response
refuses even with a later RST. Client receipt is independently observed, never
inferred from either ASGI or protocol counters. Unit/adversarial cases must
exercise real original-cycle Unix sends and all binding/type/counter/timing/
closure refusals, including PID1 and incorrect outer-PID substitution. Fresh source identity/gates and actual installed application/native/rootless
runs at both prefixes remain required for the optional runner. Synthetic cases
or old failed schema-1 evidence cannot supply its missing observations.

## Container and network proof interpretation

Network-isolation evidence must distinguish actual outcomes rather than infer
them from errno alone. A timeout with no errno is neither connect success nor demonstrated denial.
Retain the actual outcome and its limits. Native packet
filtering requires actual worker PID/start/cgroup/network-namespace binding,
read-only before/after inspection of attached ingress/egress deny-program
semantics, same-UID/same-namespace nonce controls against continuously owned
listeners, explicit fresh worker outcomes and no accepted worker tuples.
Rootless socket denial requires its exact applied protected policy/default
errno, same-image/kernel stock-policy family availability and restricted-worker
AF_UNIX success. A blanket timeout/ENOSYS allowance is forbidden. Version the
closed execution-proof schema and independently validate the conjunction;
do not weaken worker units, seccomp, SELinux or kernel settings. These are test
evidence corrections, with no new production behavior or permission.

Rootless container proof retains the raw observed `cap_drop` list and its order;
never replace measured entries with `ALL`. The two allowed encodings are literal
`["ALL"]`, or exactly11 unique strings comprising `CAP_CHOWN`,
`CAP_DAC_OVERRIDE`, `CAP_FOWNER`, `CAP_FSETID`, `CAP_KILL`,
`CAP_NET_BIND_SERVICE`, `CAP_SETFCAP`, `CAP_SETGID`, `CAP_SETPCAP`, `CAP_SETUID`
and `CAP_SYS_CHROOT`, the measured expansion in the pinned owned Podman fixture.
Order does not affect capability meaning; missing, extra, duplicate, nonstring
or other entries refuse. This closed metadata equivalence never replaces the
original observed create request for `--cap-drop=ALL`, no capability addition,
and the original role process's actual zero `CapEff` and `CapBnd`. Keep the
existing UID mapping, no-new-privileges, seccomp, read-only root, mount/network,
manager ownership and normal drain checks. No capability or container policy is
changed. A changed proof validator requires fresh source/gate identity and installed
generations, even if product artifacts remain unchanged. Earlier failures remain
failed.

Caddy listener proof retains the raw observed INET row values and order, with no
family/address normalization. Require exactly one or two rows; every row has only
`protocol`, `address`, `port` and `kernel_inode`, with string protocol/address,
exact integer port and positive exact integer kernel inode (booleans refuse).
Protocols and kernel inodes are unique. Application/native proof continues to
require `tcp`, permits only optional `udp`, and binds every row to `127.0.0.1`
at the configured origin port. Rootless proof permits only two closed alternatives:
`tcp` with optional `udp`, every row `0.0.0.0:8443`; or `tcp6` with optional
`udp6`, every row `[::]:8443`. Mixed families, UDP alone, aliases/mapped addresses,
unknown fields/protocols, duplicates or extra listeners refuse. These wildcard
addresses describe only the measured container network namespace: the unchanged
outer host publication remains bound to `127.0.0.1`, with strict private-CA/IP
TLS verification and all existing process/FD, namespace, isolation and normal
resource-drain requirements. Retained controlled observations establish the
closed encoding; missing rows from an earlier failed run remain missing. This
corrects private proof metadata interpretation, with no product, template,
publication, TLS or architectural-policy change. New canonical proof bytes need
new source/gate evidence and fresh required installed generations; do not promote
an earlier failed or unknown result.


## Accessibility, performance and coverage

Exercise keyboard navigation, visible focus, dialog focus/return, labels and
validation announcements, status/error regions, table headings, reduced motion
and contrast. Include representative 1440px/390px viewports and 200% zoom.
Covered screens require zero serious/critical axe violations; manual keyboard
and screen-reader checks supplement automation without claiming complete
accessibility conformance. Use semantic locators and bounded auto-waiting
assertions. Preserve retry counts: a retry-only pass is flaky evidence to resolve.

Performance measurements identify fixture, hardware and browser. The initial
engineering targets are at most 350 KiB gzip application JavaScript, first usable
Library within two seconds after authentication on the declared local fixture,
bounded manifest/catalog DOM and stable retained state over 100 route/refresh
cycles. Record baselines and p95 results; these are measurement targets, not NAS
latency or browser-heap guarantees. The source build enforces its gzip JavaScript
budget in [check-build.ts](../web/scripts/check-build.ts); a successful source
budget check does not establish the installed interaction targets. Large
manifest virtualization must remain keyboard accessible.

New frontend source coverage requires at least 90% lines and 85% branches, plus
every named critical auth/permission/operation/config/card decision outcome.
Backend security/administration/card modules need explicit adversarial branch
outcomes, with the initial 90% branch target where measurable. Aggregate coverage
cannot substitute for missing required cases. Keep independent wire expectations
and fixtures: generating both expectations and tested output from the same
schema cannot establish its correctness.

## Validator and regression sources

The closed schemas, bounds and acceptance conjunctions are enforced by
[check-web-functional.py](../scripts/check-web-functional.py), particularly
`transfer_protocol`, `transfer_protocol_result`, `transfer_evidence`,
`cap_drop_all`, `role_container` and listener/worker validators. Their
[adversarial regression suite](../tests/unit/test_web_functional.py) covers real
original-cycle Unix sends, counter/type/timing/binding failures, PID1 mapping,
capability encodings, listener families and network-proof disagreements.

Changing the pinned H11 implementation, fixture entrypoint or evidence validator
requires a compatible proof update and fresh observations. Do not alter product
send/receive behavior or weaken confinement to make a fixture pass. Applicable
product security remains governed by [security](security.md) and
[host administration](host-administration.md).
