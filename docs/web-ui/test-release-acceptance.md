# Candidate test-release acceptance

As of November 1, 2026, **all 95 acceptance scenarios are complete**, with
executed evidence at every required layer under the adopted product-focused
criteria. Source implementation, installed functionality, compatibility/rollback,
human guides, legacy deprecation and final handoff acceptance are complete.
Production migration remains separate.

The installed test candidate is **0.2.78**, from application source
`f829857ec045ce4616055e357e7d6aa7047287ca`. It uses matching immutable interface,
backend and helper artifacts. This is a disposable test-release identity;
repository package metadata remains **0.2.2**. No published release or production
upgrade is implied.

## What was proved

Native and guarded rootless installations use trusted test TLS through the
existing shared Caddy endpoint at `/ui/` and `/management/ui/`. Actual Chromium,
Firefox and WebKit checks cover both entrypoints in both installations. Deeper
fault, privilege and domain cases use the relevant boundary, with documented
reuse where that implementation is unchanged. Each scenario retains its required
test layers; every scenario was not repeated in every browser/profile combination.

| Area | Evidence and scope |
| --- | --- |
| Authentication and routing | Native browser Basic authentication, credential separation, bounded refusal, CSRF protections, configured-prefix routing, authenticated assets, deep links and security headers have executed application and installed evidence. Existing REST and MCP credentials retain separate authority. |
| Library, details and README | Actual filters, tags, pagination and current/retained publication views remain distinct. Model and dataset details retain exact SHA/publication identity through direct entry, reload and history. README content stays inert, external assets become placeholders, links stay pinned, and unsafe/deep content fails closed. Dataset declarations retain source attribution without model metrics or inferred counts. Files show bounded metadata, bytes, digests and explicit locator bases; raw archived files are not served. |
| Configuration | Real forms add disabled model/dataset entries and tags, validate, preview, Apply and confirm exact installed bytes. Separate retained checks cover stale-draft UI409, explicit dirty-draft discard and observation of original outcomes after reload. Final rootless configuration has29 disabled entries; all seven archived publications remain intact. No accepted Apply is repeated to obtain a clean test aggregate. |
| Maintenance and Repair | Owned fixture workflows prove reviewed retention/Prune and explicit unmanaged Purge with corresponding audits. Configuration-only removal preserves archived publications as described above. A real integrity finding leads to explicit same-SHA Repair with a distinct publication, followed by a clean exact verification. Original manifests, generations, unknown files and prior operation evidence remain preserved. These are owned local-storage effects, not production NAS tests. |
| Administration | Supported native schedule controls and matching original-observer Stop have real protected effects. Stopping the observer does not cancel accepted backend work; its later genuine completion is observed separately. Guarded rootless controls show actual denial reasons and refuse unsupported schedule/observer actions. Verification scheduling remains read-only. Installed process, socket, mount, credential and confinement observations verify the role boundaries. |
| CLI, MCP and worker | All14 read-only MCP tools and existing CLI credential classes traverse shared Caddy at both entrypoints. Native0.2.78 has actual browser/client overlap:32 CLI/MCP calls occur during nine visible Library workflows. Rootless client reads are sequential and use labelled synthetic reports. One genuine native0.2.78 revision-verification job reads eight objects/6,286bytes for one exact revision; its original result/report survive reload. Two subsequent MCP reads match that new report. Concurrency with the new worker job is not claimed. |

The guide review matches 40 documented workflow steps to retained actual installed
observations and current controls. Thirteen genuine synthetic screenshots keep
their historical build labels; 19 examples pass strict-model or inert syntax
checks. Protected provisioning, installation and refresh examples are not executed
for documentation review. Existing keyboard and screen-reader observations retain
their recorded limits; no new human-listening or universal accessibility claim is
made.

The current required source/build check **passes**:
`scripts/check.sh --require-web --with-build` exits 0 with 9,650 backend tests,
4,051 unique combined web tests and 16 wheel checks, three locked installation
profiles, two built-browser checks and the real HTTP/API fixture. All 1,547 frozen
inputs remain unchanged. Frontend coverage is 95.02% of lines and 90.13% of branches.
Legacy Cockpit validation is excluded from current acceptance. The acceptance
ledger and closure documents are reconciled after the source check and validated
separately. The optional instrumented functional runner was not run as this
acceptance path and is not claimed to have passed.

The exact previous 0.2.2 client accepts the new server's existing routes and all 14
MCP tools through both aliases in both profiles. Native literal validation/Plan
and original lookup pass; rootless positive reads/validation and two classified
credential/candidate-authority refusals are retained. Actual old copied-state
readers preserve all inputs and document unsupported formats. Both disposable
installations complete indexed78→77→78, with matching UI/backend/helper selection,
trusted TLS, Library/reload, stable subject and unchanged original-operation
outcomes. The [migration guide](migration-from-cockpit.md) records exact limits,
including the predecessor's configuration-read limitation and preserved failures.

## Retained qualifications

Original failed runs remain failed. Passing named clauses and targeted
continuations supply distinct evidence; they do not turn earlier aggregates into
passes. This applies to configuration, dataset navigation, maintenance, Repair,
schedule and worker observations.

The earlier native Library target-lookup failure remains unexplained. One later
bounded search succeeds, and direct exact-publication navigation succeeds; neither
establishes the cause or a fix. Some Firefox response events disagree with the
actual in-page response for expected refusals; their event/body attribution remains
qualified. Cross-origin form observations do not independently establish which
Basic authority the browser sent. Authenticated CSRF refusal is supported by
separately executed TLS/protocol and application tests. These limits remain in the
case records rather than being silently credited as broader browser proof.

## Final observations and handoff

Final read-only Chromium checks on the native and rootless test installations
pass trusted TLS, exact build/bootstrap identity, Library before and after reload,
unchanged administrator subject and normal context/container/cgroup closure.
They perform no domain write or external request. Original old-client GETs
return the same succeeded native and failed rootless operations; both remain
unchanged, and both temporary tunnels close normally. No accepted job is replayed.

These final checks reuse the coherent clean 0.2.78/f829 artifacts. Runtime
code, packaging and web source bytes and the normalized locked dependency
closure remain unchanged; repository self-version 0.2.2 is kept distinct. Deeper
Chromium/Firefox/WebKit and prefix evidence retains its recorded scope. This is
not a newly installed final 0.2.2 artifact, a new full browser matrix or refreshed
Firefox/WebKit trust proof. Private store preservation in final captures means
metadata continuity, not a new byte-for-byte private-payload audit.

The hfcache Cockpit plugin is deprecated. The new web UI operates independently
through its indexed API/static artifacts and existing Caddy endpoint. Legacy
source, history, licences, shared helpers and installed state remain; no further
plugin maintenance/validation or live uninstall was performed.

The [operator handoff](deployment.md#operate-the-unreleased-web-interface) links
build/provision/validation, original-handle recovery and compatible rollback.
Its production checklist remains unchecked. Original failed runs, unknown SDK
handles, Library/Firefox/form-Basic qualifications and accessibility limits stay
preserved; final acceptance does not invent their causes or broaden their scope.

This summary supplies **no production rollout or real NAS acceptance proof**.
Production archive permissions, original guards, unresolved handles, disabled
calendars and live Cockpit remain unchanged. See [deployment status](../deployment-status.md)
and the [deployment guide](deployment.md) for those separate boundaries.
