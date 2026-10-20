# Remediation design

## 1. Keep a single authenticated application transport

Retain `hfcacheArgv` / `runHfcache` as the only application-command adapter, using
the fixed rootless client launcher and its protected profile. REST continues to
own validation, execution and report reads. The browser must not receive a bearer,
accept an endpoint/image/engine override, run a Python implementation inline, or
fall back to archive-local execution after any API failure. MCP is not part of the
administrative execution path.

Do not require native `/opt/hfcache/current/.venv/bin/hfcache` or host credential
imports on the rootless profile. The host and container-visible client TOML can be
different because the helper overlays release-owned settings; diagnostics must
identify the actual selected profile without exposing its secret source contents.
Do not “repair” the rootless socket to the different native default.

## 2. Typed errors and explicit stages

Introduce a small pure normalized error model, with field validation and hard
bounds. Preserve these facts where actually known: operation category, stage,
Cockpit problem, process exit status/signal, safe operator message, retained key/ID,
original command/route and whether submission or a host mutation is uncertain.
No exception object, raw candidate, credential, arbitrary process arguments or
unbounded response is logged or persisted.

Categories must distinguish host/privilege communication, launcher/process start,
API configuration/authentication/protocol/connectivity, terminal domain failure,
and uncertain job observation. Stages include installed read, candidate write,
candidate validate, candidate preview, install, installed confirm, and operation
lookup/wait. A missing terminal Envelope cannot establish whether a host write or
job admission occurred. A valid failed Envelope is authoritative classified
output, not a spawn-schema error. Process nonzero plus a valid Envelope remains a
result except where installed confirmation also requires successful postchecks.

Map documented Cockpit `problem` codes and validated process fields to safe
messages. Unknown problem strings remain bounded diagnostic identifiers, not new
domain codes. For `reconnected`, show which observation stopped and the appropriate
next step; retain the original problem rather than asserting that the API crashed.
Raw host stderr is not trusted merely because it is short: prefer fixed,
allowlisted diagnostics. Keep server/CLI redaction and add disclosure tests.

## 3. Connection and privilege lifecycle

Own D-Bus clients at application scope, disposing subscriptions and invalidating
the cached instance on close/session/privilege transitions using supported Cockpit
APIs. Recreate read channels with a finite backoff budget; clear stale pending
results by generation. Poll failures set unavailable/stale state and cannot keep
controls enabled from an earlier observation. Avoid overlapping indefinite polls.

Separate recovering connectivity from retrying an action. Reads can be refreshed
after reconnect. Start/stop/reload unit calls, schedule writes, candidate writes,
installation and keyed jobs must not be automatically repeated. Even synchronous
candidate validation is not automatically retried as the entire multi-stage
candidate pipeline, because that pipeline writes files and may submit a plan.

Use explicit readiness states: unknown, connecting, administrative access required,
backend unavailable, API incompatible, restricted profile, and ready for the
specific action. This is UI guidance, not a replacement for server authorization,
archive identity, policy, capacity and lock checks. A healthy listener is not
archive integrity, writable NAS, or workload approval.

## 4. Configuration pipeline

Retain the existing fixed files and cooperative root-only lock. Candidate and
installed-base comparisons remain exact UTF-8 bytes, not just an operational hash.
Keep 1 MiB bounds, NUL/Unicode checks, no-follow/ownership/link checks, same-directory
atomic rename, 0640 root:hfcache, fsync ordering, and the preserved predecessor.
Changing tags may not change the operational fingerprint; exact content checks
remain mandatory before and after installed validation.

Model each stage and its acknowledgement separately. Preserve candidate validation
Envelopes independently of readiness. A recognized negative assessment is invalid
candidate input; a general HFAPI/HFARG/HFCFG refusal without assessment is a failed
request, not an incompatible-success schema. Any malformed success, unknown schema,
authority mismatch, invalid installed policy, failed required preview or stale
base prevents installation. Do not synthesize successful assessment fields.

Capture the exact draft/base in application memory for the active editing session.
On reconnect, invalidate readiness and perform guarded read-only reconciliation of
fixed candidate/installed paths against known expected content. Add only the
minimal guard inspection operation needed; no arbitrary path or mutation option.
A lost write acknowledgement can be classified as matching, absent, changed or
unknown without writing again. On a full page reload, do not infer ownership of
an existing candidate from its filename; preserve it and require explicit reload /
revalidation. Do not persist raw TOML to browser storage.

Preview is a keyed job. Capture its key before send, retain its ID and restore
observation from the operation registry. A terminal successful old preview does
not restore installation readiness after the base/draft/authority changes. Fresh
revalidation and exact comparison are still required.

After an uncertain install, never automatically roll back, remove the candidate,
repeat rename, or mark success from a matching fingerprint alone. Retain diagnostic
cause/stage, backup and expected bytes where still in memory; reacquire the same
lock, establish installed content, validate through the API, then require explicit
operator acknowledgement or a fresh preparation as appropriate. The existing
postcheck requirement cannot be weakened to accept a disconnected process with
apparent success stdout.

## 5. Submission and recovery registry

Create one bounded registry outside unmounted tabs. A record contains a schema
version, original safe idempotency key, optional operation ID, exact route/action,
minimal display metadata, trusted host/profile/API-scope evidence, timestamps and
observation state. Store only validated nonsecret recovery metadata in
session-scoped browser storage; keep retention/capacity explicit. Session storage
supports reloads in the same browser tab, not guaranteed recovery after closing
that tab, ending the session or clearing storage. Offer safe handle copy/export
and explicit server-history lookup guidance for that case; never claim browser
state has the durability of server receipts. Never persist credentials, full
configuration, raw logs, response bodies or arbitrary user text.
Treat browser storage as untrusted input, not command authority.

For every keyed action, generate a safe unique key before starting the submit
process, persist it, and pass it as the existing global CLI `--idempotency-key`
option in fixed argument construction. The CLI must print the same key; a mismatch
is a refusal. This closes the gap where a channel could fail before the CLI's
pre-send notice reaches JavaScript. Validate and keep key arguments as data; never
interpolate them into a shell script. No key is attached to synchronous validation.

Retain scope from validated client/receipt evidence, not a browser-selected API
URL. At minimum distinguish the Cockpit target host, fixed deployment/client
profile and endpoint, REST credential class, and known archive UUID. Do not infer
archive UUID from a pathname. If existing CLI output does not expose sufficient
safe authority data, add a narrow, documented presentation of already validated
client metadata, not new credentials or arbitrary routing. Before any evidence is
available, mark the record's authority unconfirmed; do not silently bind it later
to a different endpoint. No auto-lookup across a changed or unverifiable scope.

Lifecycle is prepared -> submission uncertain or accepted -> observing -> exact
terminal result, with distinct expired/missing/unavailable-history states. A key
printed/generated is not proof of admission. A 202 is not completion. A 404 or
expired history is not proof of nonexecution. No automatic POST replay is added,
including same-key replay: recover by lookup/wait first. Unknown results remain
visible and block accidental repeat of that action. A new deliberate submission
requires the existing confirmation and fresh policy/preview checks after resolution
or a documented operator decision; do not erase the old record to enable it.

Integrate every keyed operation, including candidate sizing, installed plans,
doctor, maintenance dry runs and applies, repair, selected/full sync and all
non-estimate verification. The maintenance predicate must consider registry and
caught-error uncertainty, not just `[dryRun, applied]`. Synchronous reads and
validation must not be mislabeled admitted jobs.

Provide explicit in-page `operations lookup -- KEY` / `operations wait -- ID`
through the same fixed launcher. Wait is observation only. Copyable commands must
include the same service identity / fixed profile and safe handle quoting, with no
bearer. Page close, AbortSignal, Stop observing and callbacks never cancel server
execution or stop the actual API/private worker. Bounded polling/events remain the
existing protocol; add no SSE or WebSocket assumption to the REST API.

## 6. Manual jobs, schedules and guarded profiles

Amend CP-04 before switching manual full sync to CLI `sync` and manual full verify
to `verify --full`. Both follow the same keyed admission/observation path as
selected jobs. Display server operation state, not systemd observer exit status,
as the source for these jobs. Schedule state remains a separate host concern.

Implement a small fixed, read-only host-profile inspection boundary if necessary
to report supported deployment/launcher binding, system-unit availability and
known guard state. It may not return secrets or accept caller-selected executables,
paths or managers. Unknown/mixed/drifted state is unavailable, not a write-enabled
fallback. Absence of a guard or mask alone is not sufficient authorization: use
explicit trusted, administrator-provisioned supported-profile evidence for the
permitted case. Test fixtures may inject that evidence; browser input may not.

On the selected guarded profile, disable all prohibited archive-effecting actions
consistently (including maintenance apply and actual verification), retain ordinary
metadata/validation, and explain existing holds. Candidate sizing and doctor are
not “pure local reads”: they can contact Hub and create control receipts. Their
availability must respect the recorded operational scope. Never modify masks,
guards, exports or credentials to make a UI test pass.

Keep approved schedule changes on the fixed system manager and validated fixed
drop-in. Disabled/masked/unavailable schedule profiles cannot write a drop-in merely
to fail at a later restart. Full scheduled observers, where independently deployed
and allowed, remain separate from manual jobs. No user-manager redirection or
`hfcache.target` operation is added, and the verify timer stays display-only.

## 7. Reports and read-result rendering

Add typed read-only `runs list` and `runs show RUN_ID` CLI adapters for existing
`GET /api/v1/runs` and `/runs/{run_id}`. These names are proposed additions: the
baseline has SDK/HTTP routes, not these CLI commands. Freeze output and pagination
contracts first; validate IDs and return exact classified server Envelopes, not a
bare response wrapper or synthetic success. Use the existing typed client's
bounded reads and identity checks. No CLI mode accepts an arbitrary path or URL.

Use explicit bounded pages for the UI where feasible; document whether each CLI
call emits one page or a fully bounded reconstruction. Do not append unbounded
pages or silently truncate reports. Stale/invalid cursors, missing reports,
malformed schemas and UUID/run-ID mismatches are visible refusals. Distinguish run
IDs from operation IDs and preserve historical report identity. Adapt the UI from
filenames to actual report metadata/IDs; do not assume the old raw file shape is
the HTTP wrapper shape.

Remove `ls`/`cat` report reads once parity passes. Host journal correlation remains
an optional, bounded diagnostic with line/byte/time limits and explicit truncation.
It cannot establish domain outcome and cannot block report access when unavailable.

Use consistent result wrappers on every read surface. Render a valid nonzero
Envelope before accessing success-only fields; distinguish empty from unavailable;
show safe partial result data only as such. Version already calls `version
--server`: retain it and correct documentation, but add the missing error alert.
A refresh failure must not leave prior healthy data looking current or authorize
a mutation. Preserve `EnvelopeAlert`, error codes, partial results and strict
unknown-schema refusal rather than turning every domain exit into a JavaScript
exception.

## 8. Validation and deployment evidence

Extend pure tests, component rendering/lifecycle tests and temporary filesystem
fixtures with the matrix cases. Exercise the actual CLI process over a private
Unix socket, not solely an injected return value. Add a browser/adapter harness
that controls realistic Cockpit rejection objects and async streams. Then run the
exact privilege/systemd/rootless launcher chain in a provisioned disposable
Cockpit environment without NAS, with an immutable fixture release and synthetic
credentials. Never call a browser shim “real PAM acceptance”.

Use the repository's frozen toolchain and full gates. A skipped Cockpit stage is
not passing coverage. Record application commit, browser bundle identity, physical
launcher/profile binding and image digest separately; package version alone is
insufficient to rule out deployment skew. Final release handoff keeps separate
source, disposable-runtime, installed-Cockpit and NAS/workload acceptance fields.
No source task silently performs deployment or clears a production hold.
