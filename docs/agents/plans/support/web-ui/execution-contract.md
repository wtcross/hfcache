# Resolved execution contract

WEB-001 accepts these design boundaries against exact baseline
`6b8fae2e0997403ae5c716a2e92148af0a972af9`. They are implementation requirements,
not implemented feature claims. Standing contracts/ADRs state their conformance
gaps. Changes during implementation require explicit amendments and evidence.

## WEB-023–026 execution amendment (2026-11-01)

After WEB-022/9d11738, the [bounded-testing policy](testing-strategy.md#web-023026-bounded-product-testing-and-effort)
governs remaining tasks under adopted product-focused acceptance. All product
authority, safety boundaries, scenarios and minimum layers remain. Historical
runner lifecycle/proof details below stay strict for optional diagnostic use;
they do not require new machinery or a mandatory85×18/95×18 acceptance path.
Valid evidence reuse is not new execution. Original baseline records remain.

Latest user amendment,2026-11-01: explicitly “ignore the cockpit plugin moving
forward” and deprecate it once the new web UI is complete. This supersedes
pending legacy-plugin validation, exhaustive retirement inventories, harness
ports, dependency cleanup and source/live removal obligations. Preserve legacy
source/history/licenses, generic clients/runtime helpers and the live install.
WEB-025 is a proportional deprecation/handoff; RELEASE-08 still requires actual
new-web independence evidence at its existing minimum layers. All95 underlying
new-web behaviors and remaining WEB-023/024/026 requirements remain. No pass or
execution is supplied by this amendment.

## Baseline and decisions

No source drift exists. Initial checkout was `main`, with only this intended
bundle untracked. No WEB IDs or `feat/web-ui` branch existed and the selector was
inactive. Activation preserves every historical task, rollout restriction and
original unknown operation/candidate. The source audit reconfirmed existing
catalog/maintenance/job routes; none needs a duplicate UI endpoint.

Allocated decisions: 140 authentication/static serving, 141 protected host and
configuration administration, 142 card adjuncts, 143 frontend/tool gates, and
144 conditional Cockpit retirement. That historical proposed retirement scope
does not override the later explicit user deprecation amendment above.
Dependency versions are selected and verified in WEB-002/004/014, as required by
their tasks; this package adds no runtime dependency.

## Frozen route delta

The deployable UI is static content inside the existing API image. Per the
2026-10-20 implementation clarification, retain its pinned UBI 10 micro build and
runtime FROM stages and existing donor restrictions. Do not add a frontend image,
runtime Node/package manager or larger general-purpose runtime base. WEB-021
must prove base ancestry and installed contents using exact image identities.
Unshipped browser test tooling has a separate dependency identity and provides no
evidence about the product image base.

Paths below are relative to `/api/v1`, except `/ui/`. Existing route DTOs,
capabilities, Envelopes, credential classes and MCP's fourteen tools stay strict.

| Method | Path | New authority |
| --- | --- | --- |
| GET | `/config` | `config-read` plus protected helper policy |
| POST | `/config/applications` | `config-write` plus protected helper policy; keyed |
| GET | `/repositories/{type}/{namespace}/{name}/publications/{sha}/{publication_id}/card` | existing REST read |
| GET | `/host/status` | `host-read` plus protected helper policy |
| POST | `/host/sync-schedule/validations` | `host-read` plus schedule policy |
| POST | `/host/sync-schedule/changes` | `schedule-write` plus schedule policy; keyed |
| POST | `/host/sync-observer/stops` | `observer-stop` plus observer policy; keyed |
| GET | `/host/journal` | `host-read` plus diagnostic policy |
| GET/HEAD | `/ui/`, recognized navigation, indexed assets | Basic administrator |
| GET | `/ui/bootstrap.json` | Basic administrator; independent schema 1 |

Extend `/config/validate` and `/plans` with one mutually exclusive `managed`
alternative; do not change omitted or literal `candidate` canonicalization.
Unknown, mixed, null and coerced alternatives refuse. New versioned assessment
payloads apply only to the managed form. No tag CRUD, cancel, payload, card
refresh, scheduler, generic shell or arbitrary systemd endpoint is authorized.

## Managed configuration

`ManagedEditRequest` is `{base_revision, edits}`; schema version is conveyed by
the versioned containing projection. `base_revision` is an opaque authenticated
binding to schema, archive UUID, fixed target and **complete exact bytes**,
using a protected stable random HMAC key. It is not a raw configuration hash.
Maximum installed/candidate text is 1 MiB UTF-8. Maximum edits is 256. Reject
repeated repository identities and allow at most one settings-replace, rather than
making ordering significant. The closed edit union is:

- `{kind: "repository-upsert", repository: <existing RepositoryConfig fields>}`.
- `{kind: "repository-remove", repository_type, repository_id}`.
- `{kind: "settings-replace", settings: <nonempty closed nested object>}`. Its
  optional children are `storage`, `sync`, `verification`, `repair`, each a
  nonempty object of supported field replacements; dotted keys refuse.

Editable settings are `storage.publication_mode`, `storage.minimum_free_space_gib`,
`storage.minimum_free_space_percent`, `storage.maximum_revisions`, the existing
`sync` fields, `verification.lock_wait_seconds` and
`repair.retired_instance_grace_hours`. Every value uses its current strict
configuration constraint. All Hub fields, root/UUID, schema version, required
hashing/algorithm, server/auth/helper/listener and filesystem paths are protected.
Read projection contains only editable values, constraints and fixed protected-field
explanations. No secret/redaction placeholder can be round-tripped as a value.

Reconstruct one deterministic TOML candidate on the server from the fresh full
base; preserve protected values, repository order for existing entries and
canonical order for additions. Show any serialization/comment changes in review;
the preserved predecessor contains original bytes. Validation, sizing and Apply
use that same reconstruction and opaque candidate binding. Upsert replaces all
supported repository fields, including normalized tags and declared dependencies.
Remove changes configuration only. Read never creates locks or adopts candidates.

Apply body is `{managed: ManagedEditRequest, preview_operation_id}`. Preserve the
existing `selectorsNeedingPreview` rule from `cockpit/src/lib/config.ts`: derive
the exact **newly added, newly enabled or revision-retargeted enabled repository
set** server-side. The managed form requires selectors omitted or empty, never
a caller-selected subset. A nonempty required set needs successful complete
Hub sizing for that exact set/resolved revisions/candidate/base/archive and
independent Hub permission. Tag-only, settings-only, removal-only and other
empty-required-set edits retain the existing no-Hub rule. After syntax/authority
validation they receive an explicit successful no-Hub managed assessment; the
bound assessment operation is still required. This preserves an existing class
rule rather than inventing a tag exemption, and lets configuration-only guarded
profiles edit tags without granting Hub authority. Mere HTTP 200 or client
assertion grants nothing.
Helper checks that bound managed assessment against
the fixed local receipt/result store read-only, not an arbitrary posted result.
No raw configuration is persisted in generic receipt/event/result data.

## Privileged boundary and uncertainty

The application remains unprivileged. Helper protocol schema 1 uses finite
length-prefixed UTF-8 JSON over one protected AF_UNIX socket, at most 2 MiB per
frame (independent of the 1 MiB decoded candidate/base limits), one request per
connection and finite deadlines. Preparation sends managed edits and an opaque
base binding; base and candidate are reconstructed in the protected workspace,
never sent together as raw documents. A candidate-only response must also fit
the encoded frame bound; excessive JSON expansion refuses. No descriptor
passing, shell command, caller path, unit, manager,
credential or archive selector is accepted. Requests have `schema_version`,
`request_id`, `operation`, and strict operation-specific `body`; responses bind
the same identity and a closed outcome. Operations are `status`, `config-read`,
`config-prepare`, `config-apply`, `outcome-read`, `schedule-validate`,
`schedule-change`, `observer-stop`, `journal-read`. Unknown keys/versions refuse.

Socket owner/mode and actual SO_PEERCRED mapping are pinned to protected
deployment configuration. Rootless mapping needs real process/namespace proof;
a supplied principal/UID is not that proof. Helper independently checks indexed
physical release/config/profile and six-category host policy before effects.
Bearer writers receive no new administrative capabilities. API authentication
and permission checks precede body parsing; helper policy grants no browser login.
Helper never contacts Hub, opens archive payloads or gains archive-write authority.

Preserve `/etc/hfcache/.configuration.lock`, `.candidate.toml` and `config.toml.bak`
semantics from the legacy pipeline. A conflicting candidate or unexplained backup
refuses; no automatic adoption/deletion. A prior backup positively bound to a
confirmed helper outcome is copied durably to that operation's protected evidence
and exact-checked before replacing the fixed backup with the new predecessor.
Preserve unknown/legacy backups for explicit reconciliation rather than silently
overwriting them. This allows subsequent confirmed applications without deleting
the earlier predecessor. Preparation holds the existing flock only while
snapshotting exact bytes. All validation/Hub sizing runs outside it. Apply tries
the same noncreating original lock nonblocking, rechecks base/candidate/preview,
durably preserves predecessor, atomically installs 0640 root:hfcache, fsyncs and
checks exact content plus operational fingerprint before confirmed success.

API receipt-store/admission locks are released before helper calls. Helper local
outcome-store lock may precede its nonblocking config flock; neither crosses a
network/API call or archive lock. Read-only assessment lookup is bounded and
does not acquire API writer locks. No API path holds a config lock while waiting
for domain work. This avoids a legacy client holding the config lock while its
preview waits in the same mutation lane. Busy refuses rather than waiting in a
lock cycle. Already admitted domain jobs keep their immutable policies.

Independently version helper outcomes under a protected local 0700 workspace,
0600 records. Persist intent before effects and retain candidate/predecessor
material associated with uncertainty. Resource ceilings refuse admissions, never
evict unresolved records. API restart does not dispatch helper mutations again.
Original-key/ID lookup uses outcome-read and exact guarded reads only. Outcomes
are `unchanged`, `confirmed`, `installed-unconfirmed`, `conflict`, `unknown`;
missing history never becomes unchanged. No rollback/cleanup/replay route.

## Fixed host controls

Native positive controls require a proven indexed system-manager binding.
Selected rootless schedule/observer permissions stay false; never substitute
same-named user units. Status includes bounded six-category effective permission
reasons, fixed unit facts, schedule and opaque schedule revision; helper failure
is unknown/unavailable, not inactive. Verification timer is display-only.

Schedule validation accepts `on_calendar` (1–4096 printable ASCII bytes without
backslashes) and `randomized_delay` (1–256 printable ASCII bytes without
backslashes), invokes fixed systemd-analyze
argv with bounded output/deadline, and writes nothing. Change is a discriminated
union `pause|resume|replace|reset`, always with `expected_revision`; replace alone
carries validated calendar/delay. Observer stop requires exact expected invocation
ID and fixed scheduled-observer identity. It never cancels accepted work.
Journal source enum is `sync|verification|api|worker`, limit 1–200, opaque cursor,
maximum 64 KiB projected page. No arbitrary journal predicates or paths.

## Authenticated assets and principal

One protected schema-1 administrator record supplies stable subject, username
and Argon2id hash. Initial verification target is m=65536 KiB, t=3, p=1,
salt=16/hash=32 bytes; WEB-004 benchmarks this before acceptance. Header <=8192
bytes; decoded username <=128 and password <=1024 UTF-8 bytes; record <=8192.
Admission permits two active verifications/eight waiting, with a bounded global
30-failure/60-second window; throttled work does not perform Argon2. Cheap limits
run before verification only for the configured Basic flow; existing bearer,
missing and disabled-provider authentication error precedence stays unchanged.
Every authenticated request still receives the same bounds.
Use a dedicated bounded executor off the ASGI event loop,
independent of metadata/operation observation pools. Recheck the failure window
when queued work starts; request cancellation releases capacity only after the
actual hash work completes. Validate protected PHC algorithm/version and exact
selected m/t/p/salt/hash parameters at startup before any verification, so an
otherwise syntactically valid record cannot choose unbounded hash work.
Wrong-user verification performs equivalent hash work.

Principal includes stable subject, method, credential class and internal capability
set. Existing public class values remain unchanged. Basic maps original keys
through a domain-separated stable-subject digest before store lookup; include a
NUL/domain and length-framed subject/key in the hash preimage, outside the legacy
printable raw-key grammar. Do not translate to a printable raw key that a bearer
could submit to collide with the Basic namespace. Bearer key digests remain
byte-identical. Private human attribution is separately
versioned; old receipts are never retroactively attributed to a person. UI schema-1
bootstrap exposes only safe subject/display, effective capabilities/reasons,
configured archive UUID (without claiming a live sentinel/health check),
UI/server contract/build identity and configured relative paths.

Unsafe Basic requests require one exact configured HTTPS Origin, JSON and
`X-Hfcache-Request: 1`. No-Origin bearer compatibility remains. Basic never
authenticates MCP. Every UI route authenticates; SPA fallback is recognized
GET/HEAD navigation only. Public prefix is server configuration, never headers.
No new Caddy instance/listener/file-server/global Basic gate is introduced.

Static release manifest schema 1 pins source commit, contract version, lock and
toolchain digests, licenses and each member's path/size/SHA256/MIME. Limits:
4096 members, 64 MiB total, 8 MiB/member and 2 MiB manifest. Initial MIME allowlist:
HTML, CSS, JavaScript, JSON, PNG, WebP and WOFF2, with `text/plain` only for the
required root `THIRD_PARTY_NOTICES.txt`. No SVG, source maps, unindexed
members, symlinks or special files. Enabled missing/mismatched assets fail startup;
disabled UI leaves backend-only installation independent. Validate immutable
members once at startup through protected no-follow descriptors and capture their
immutable bytes under those bounds. Retain one root descriptor and a finite DFS
stack while capturing; do not retain4096 member descriptors. No request path is
reopened. The two rendered shell variants add at most16MiB and the manifest2MiB,
for an82MiB retained byte-payload bound, not a process RSS claim. Mount identity
mapping rejects archive/policy/state/credential/listener aliases without opening
the archive. Streams have16 active slots/no queue,64KiB chunks and a30-second
absolute send deadline including response headers; shutdown joins actual streams
before releasing capture and the instance lock. Disabled UI performs no asset
or mount-table I/O. See [decision147](../../../../adr/decision-147.md) for exact
bootstrap/manifest/prefix/lifecycle authority and [schema18.3](../../../../schemas.md#183-web-release-manifest-and-ui-bootstrap).

## Static streaming execution-proof schema2

This is private fixture evidence, not an API, durable product format or change to
the application. Preserve failed schema1 reports and their original counters;
never upgrade them retrospectively. New required stalled-send/disconnect evidence
uses exact integer `schema_version: 2`. A normal ASGI `send` await return records
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
closure refusals, including PID1 and incorrect outer-PID substitution. Fresh
source identity/gates and actual installed application/native/rootless runs at
both prefixes remain required; synthetic cases or old failed schema1 evidence
cannot close the task or the95-case matrix.

## Cards

RepositoryCard schema 1 is a new adjunct at
`published/metadata/cards/{models|datasets}/{namespace}/{name}/{sha}/{publication_id}.json`.
Fields: `schema_version`, `kind="repository_card"`, `archive_id`, `repository_type`,
`repository_id`, `commit_sha`, `publication_id`, `publication_generation`,
`manifest_path`, `manifest_digest`, `source_path`, `expected_source_sha256`,
`captured_at`, `presentation_version="markdown-1"`, `state`, `markdown`,
`presentation_sha256`, `diagnostics`. Source is root manifest-listed `README.md`
or null for absence. Durable states: `present|absent|unsupported|oversize|unsafe|failed`.
Only present has Markdown/presentation digest. Read projection adds explicit
`not_captured` for missing adjunct; vanished exact publication is HTTP 404.
Diagnostics are fixed codes, never source fragments or arbitrary exception text:
`readme_absent`, `source_oversize`, `presentation_oversize`,
`source_digest_mismatch`, `source_changed`, `invalid_utf8`,
`unsupported_markdown`, `unsafe_content`, `secret_suppressed`, `work_limit`,
`read_failed`. Non-absent states retain source identity even when presentation
fails; absent alone has null source path/expected digest.

Raw source <=1 MiB; UTF-8 **and JSON-encoded presentation body** each <=1 MiB;
whole durable record <=2 MiB. Charge existing shared source-read/work/attempt
budgets and bound aggregate serialized adjunct writes to 128 MiB per invocation.
Failure stops capture with explicit classification and preserves publication
success/evidence. Source SHA256 comparison is bounded README-only provenance,
never a verification result. No other payload hashing expansion is authorized.
Sanitize before output/hashing; GET opens only adjunct/authoritative metadata,
never payload/Hub/credentials/locks, never captures or resurrects removed content.

## Evidence delivery

`acceptance-evidence.json` names planned exact layer tests for all 95 scenarios;
every row starts pending with no executions. Implementing owners must create
covering tests and record real source/artifact/profile/command/node/outcome facts.
Plan tests validate allocation and reject a completed row with only planned tests.
They establish no AUTH/ROUTE/CONFIG/CARD/host/UI functional acceptance.
WEB-002 proves the preliminary shell in a real browser; WEB-004/005 introduce
native challenge and real Caddy/installed API coverage, with later tasks extending
that harness continuously. Required missing prerequisites block their task.

Network-isolation evidence must distinguish actual outcomes rather than infer
them from errno alone. A source audit found the original fixture encoded
TimeoutError(errno=None) identically to connect success; neither inference is
accepted from that old record. Preserve original failed evidence. Native packet
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
changed. Preserve earlier failures; changing the canonical proof validator needs
a new source/gate identity and fresh required installed generations, even when
the product package and UI inputs remain unchanged.

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

Actual native startup additionally exposes a baseline identity conflict: the
manager-created listener has kernel peer UID0 while the unchanged worker-owned
socket node has the service UID. Preserve both authorities and namedFD3 rather
than modifying socket ownership or weakening a check. Decision148 adds explicit
`verification.expected_socket_owner_uid`, defaulting to the existing resolved
peer UID when omitted. WEB-005 includes this prerequisite compatibility amendment,
its independent negative tests and actual installed native proof. Source8's green
gate remains historical evidence; new source, audited transport/build inputs,
wheel/assets and installed native/rootless profiles require fresh identity and
gates before completion. No existing source or failed fixture is reset or hidden.
