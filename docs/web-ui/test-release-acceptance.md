# Candidate test-release acceptance

As of November 1, 2026, the 85 acceptance scenarios in the installed functional review have
been reconciled against executed unit, integration and installed workflow
evidence. **Installed functional acceptance is complete.** The
remaining ten scenarios belong to compatibility/rollback, human documentation,
Cockpit retirement and final handoff tasks; overall plan acceptance is incomplete.

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

The required source/build check **passes**:
`scripts/check.sh --require-web --require-cockpit --with-build` exits0 with
9,646 backend,4,051 combined frontend,581 Cockpit and16 wheel checks, three
locked installation profiles, two built-browser checks and the real HTTP/API
fixture. All1,545 frozen inputs remain unchanged. Frontend coverage is95.02%
of lines and90.13% of branches. The acceptance ledger and closure documentation
are reconciled after that source check and validated separately. The optional instrumented functional-runner command was not run as
this acceptance path and is not claimed to have passed.

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

## What remains

The remaining work is real older-client compatibility and evidence-preserving
format/rollback drills, the complete guide walkthrough and screenshots, conditional
Cockpit source retirement, final validation and operator handoff. Their ten
acceptance scenarios remain pending.

This summary supplies **no production rollout or real NAS acceptance proof**.
Production archive permissions, original guards, unresolved handles, disabled
calendars and live Cockpit remain unchanged. See [deployment status](../deployment-status.md)
and the [deployment guide](deployment.md) for those separate boundaries.
