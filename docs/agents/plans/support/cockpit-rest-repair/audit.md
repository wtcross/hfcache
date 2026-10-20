# Cockpit / REST alignment audit

**Review baseline:** `dcc2c562b52304541d0cb85d20fc046072038e79` on `main`, retrieved through the connected GitHub
source reader. **Date:** 2026-10-19, America/New_York. **Method:** pinned static
source/contract review, with official Cockpit API documentation checked for the
process-error contract. This is not an installed-host diagnosis or a passing test
report. Findings use symbols as stable locators; follow the pinned links for exact
source rather than relying on a possibly shifted line number.

## Executive result

Cockpit is already an API client indirectly through the CLI. The migration's weak
points are the boundaries around that client: bridge error and reconnect handling,
configuration failure/result interpretation, operation recovery state, host-service
assumptions, and the remaining report-read exception. Replacing the transport with
browser `fetch()` and a token would discard existing security rather than fix these
problems.

The exact `reconnected` message is consistent with a rejected Cockpit operation
being surfaced without context. Source establishes that propagation route; it does
not establish which deployed process or session generated the rejection, whether
an HTTP request was sent, or whether the daemon failed. There is no basis here to
assert that the API socket, token, candidate mount or MCP server caused it.

## F01 — P1: bridge failures lose their problem, process and stage information

**Classification:** confirmed static error-model gap; live trigger unverified.

[cockpit/src/lib/runner.ts](https://github.com/wtcross/hfcache/blob/dcc2c562b52304541d0cb85d20fc046072038e79/cockpit/src/lib/runner.ts) (`HfcacheSpawnError`, `runSpawned`) retains
only a bounded message, diagnostic tail and optional key/operation ID. When no
terminal Envelope exists, an `Error` rejection's message is used directly.
The Cockpit `problem`, `exit_status` and `exit_signal` fields are not retained.
[cockpit/src/components.tsx](https://github.com/wtcross/hfcache/blob/dcc2c562b52304541d0cb85d20fc046072038e79/cockpit/src/components.tsx) (`QueryError`) prints that message but not
the stored diagnostic tail, and applies the same accepted-work warning to reads,
file operations and jobs. [cockpit/src/api/config.ts](https://github.com/wtcross/hfcache/blob/dcc2c562b52304541d0cb85d20fc046072038e79/cockpit/src/api/config.ts) (`mutate`,
`readInstalledConfig`) also exposes raw Cockpit promise failures outside the runner.

Consequently, an `Error` with message `reconnected` and no terminal output can
reach the page without enough information to tell a privilege/bridge transition
from a launcher failure or REST observation failure. Plain-object rejections also
need normalization; a cast to `Error` is not a runtime validation.

**Repair:** retain validated structured fields, operation kind and configuration
stage in a bounded error type; render safe diagnostics and actionable, contextual
recovery. Preserve exact successful or failed terminal Envelopes even when process
exit is nonzero. Never diagnose domain outcome by parsing stderr. Do not simply
replace `reconnected` with another generic message.

## F02 — P1: candidate validation can hide the actual API refusal

**Classification:** confirmed control-flow defect.

[cockpit/src/lib/config-pipeline.ts](https://github.com/wtcross/hfcache/blob/dcc2c562b52304541d0cb85d20fc046072038e79/cockpit/src/lib/config-pipeline.ts) (`prepareConfiguration`) passes
every returned Envelope to `candidateAssessment`. That function requires candidate
assessment fields (`valid`, `syntax_valid`, `installed_policy_valid`, authority
compatibility and mismatch list) before considering whether the response is an API
or local-client failure. A valid failed `config validate` Envelope with `data={}`
cannot satisfy that shape and becomes “Configuration validation evidence is
incompatible; update the CLI and plugin”. The page only stores validation after
preparation returns, so the original code and message can disappear.

This differs from a truly invalid candidate: [src/hfcache/services/candidates.py](https://github.com/wtcross/hfcache/blob/dcc2c562b52304541d0cb85d20fc046072038e79/src/hfcache/services/candidates.py)
returns explicit negative assessment fields for that case. Transport/auth/config
refusals are not negative assessments. The typed command route and client contracts
permit failure results without candidate data:
[src/hfcache/api/commands.py](https://github.com/wtcross/hfcache/blob/dcc2c562b52304541d0cb85d20fc046072038e79/src/hfcache/api/commands.py), [docs/api-client.md](https://github.com/wtcross/hfcache/blob/dcc2c562b52304541d0cb85d20fc046072038e79/docs/api-client.md).

**Repair:** preserve and classify valid failed Envelopes before successful-assessment
parsing. Keep a strict assessment validator for actual candidate assessments;
unknown/malformed success data remains a refusal. A failed validation never creates
an install proposal or triggers sizing. Keep field errors and general API errors
separate without losing either.

## F03 — P1: configuration stage uncertainty and preview recovery are incomplete

**Classification:** confirmed state/evidence gap, not a defect in the atomic guard.

[cockpit/src/configuration.tsx](https://github.com/wtcross/hfcache/blob/dcc2c562b52304541d0cb85d20fc046072038e79/cockpit/src/configuration.tsx) sets `diskGuard` only after an
acknowledged candidate write. A lost acknowledgement may leave a candidate on disk
while the UI has not recorded that phase. [cockpit/src/api/config.ts](https://github.com/wtcross/hfcache/blob/dcc2c562b52304541d0cb85d20fc046072038e79/cockpit/src/api/config.ts)
submits candidate plans without an `onNotice` consumer. The plan is a keyed API job,
not synchronous validation. [cockpit/src/lib/config-pipeline.ts](https://github.com/wtcross/hfcache/blob/dcc2c562b52304541d0cb85d20fc046072038e79/cockpit/src/lib/config-pipeline.ts)
(`installConfiguration`) correctly refuses uncertain installation but replaces all
underlying errors with one generic error, losing diagnostic cause and stage.

**Repair:** explicit read/write/validate/preview/install/confirm states and exact
read-only reconciliation. Keep the captured draft in memory across a transient
bridge interruption, invalidate readiness on session/authority/content changes,
and never delete or overwrite an unproven candidate as error cleanup. Retain
preview key/ID before the final result. After lost install/confirm acknowledgement,
retain backup and require exact installed-content checks plus fresh validation;
do not automatically reinstall, roll back or announce success.

## F04 — P1: navigating away destroys recovery handles

**Classification:** confirmed component-lifetime defect.

[cockpit/src/app.tsx](https://github.com/wtcross/hfcache/blob/dcc2c562b52304541d0cb85d20fc046072038e79/cockpit/src/app.tsx) uses `mountOnEnter` and `unmountOnExit`.
[cockpit/src/hooks.ts](https://github.com/wtcross/hfcache/blob/dcc2c562b52304541d0cb85d20fc046072038e79/cockpit/src/hooks.ts) (`useOperationHandles`) keeps key/ID only in
component state. [cockpit/src/sync.tsx](https://github.com/wtcross/hfcache/blob/dcc2c562b52304541d0cb85d20fc046072038e79/cockpit/src/sync.tsx),
[cockpit/src/verify.tsx](https://github.com/wtcross/hfcache/blob/dcc2c562b52304541d0cb85d20fc046072038e79/cockpit/src/verify.tsx) and [cockpit/src/maintenance.tsx](https://github.com/wtcross/hfcache/blob/dcc2c562b52304541d0cb85d20fc046072038e79/cockpit/src/maintenance.tsx)
use those local handles, and some non-streaming plan/diagnostic/apply paths do not
subscribe to notices at all. The runner deliberately does not cancel accepted
server execution when a display detaches, so unmount can remove recovery UI while
execution continues.

**Repair:** central bounded operation registry outside individual tabs, integrated
with every keyed route. Persist only validated, nonsecret handles and minimal
scope/intent metadata before transmission. Restore lookup/wait, not a submission.
Keep original history on timeout, missing/expired receipts, logout/host changes and
corrupted browser storage. No token, TOML or raw log persistence.

## F05 — P1: a failed maintenance Apply can be offered again while uncertain

**Classification:** confirmed UI predicate defect; no duplicate archive mutation
was executed in this review.

In [cockpit/src/maintenance.tsx](https://github.com/wtcross/hfcache/blob/dcc2c562b52304541d0cb85d20fc046072038e79/cockpit/src/maintenance.tsx) (`DryRunApplyCard`), `uncertain` examines
only `[dryRun, applied]` Envelopes. It ignores the caught `error`, including a
`HfcacheSpawnError` with a retained key or operation ID. Applying clears `applied`
but retains the successful earlier dry run. After an apply observer failure,
`busy` becomes false, the old dry run still classifies as success, and `canApply`
can become true again. The function does not subscribe to `onNotice` either.

**Repair:** gate on the shared operation state, including pre-acknowledgement and
spawn-error uncertainty, not only on terminal Envelopes. The unresolved original
operation must be observed before a new deliberate apply is considered. A preview
never supplies future mutation authority; keep existing server-side revalidation.
Test the exact old-successful-preview / apply-failure sequence.

## F06 — P1: closed D-Bus clients and failed polls can leave a stale host UI

**Classification:** confirmed lifecycle gap; no assertion that it caused candidate
validation's specific spawn failure.

[cockpit/src/api/systemd.ts](https://github.com/wtcross/hfcache/blob/dcc2c562b52304541d0cb85d20fc046072038e79/cockpit/src/api/systemd.ts) caches a D-Bus client forever with `??=` and
has no close/invalidation/recreation path. [cockpit/src/hooks.ts](https://github.com/wtcross/hfcache/blob/dcc2c562b52304541d0cb85d20fc046072038e79/cockpit/src/hooks.ts)
(`useUnitPoll`) swallows polling rejections and retains previous state. Controls
can therefore continue to reflect old or unknown system-unit state rather than
showing an unavailable connection.

**Repair:** own/dispose clients through a shared connection lifecycle; recreate
only for reads after close or privilege changes, bound reconnect attempts, discard
out-of-generation results, and mark stale/unknown state. Never automatically
repeat StartUnit, StopUnit, drop-in writes, or API jobs. Keep the fixed system bus;
a reconnect is not permission to use the rootless user manager instead.

## F07 — P2: manual full-job controls still rely on unavailable legacy services

**Classification:** intentional retained architecture with poor UI alignment;
changing transport requires an explicit contract amendment.

[cockpit/src/sync.tsx](https://github.com/wtcross/hfcache/blob/dcc2c562b52304541d0cb85d20fc046072038e79/cockpit/src/sync.tsx) and [cockpit/src/verify.tsx](https://github.com/wtcross/hfcache/blob/dcc2c562b52304541d0cb85d20fc046072038e79/cockpit/src/verify.tsx) start full
jobs through the system bus. Buttons check running state but not the known
masked/unavailable profile. [docs/cockpit.md](https://github.com/wtcross/hfcache/blob/dcc2c562b52304541d0cb85d20fc046072038e79/docs/cockpit.md) and
[docs/adr/decision-122.md](https://github.com/wtcross/hfcache/blob/dcc2c562b52304541d0cb85d20fc046072038e79/docs/adr/decision-122.md) explicitly say these legacy controls are
blocked on the selected guarded rootless installation. This is not evidence that
retargeting them to user units is allowed.

Meanwhile [docs/api.md](https://github.com/wtcross/hfcache/blob/dcc2c562b52304541d0cb85d20fc046072038e79/docs/api.md) and [src/hfcache/api/commands.py](https://github.com/wtcross/hfcache/blob/dcc2c562b52304541d0cb85d20fc046072038e79/src/hfcache/api/commands.py)
already provide keyed `POST /syncs` and `POST /verifications` (`mode=full`, CLI
`verify --full`). Manual actions can use those established operations after
contract-first repair, while scheduled observers and timer management remain host
operations. The UI must still disable workloads on the guarded profile and show
why; neither a writer bearer nor administrative access clears the hold.

## F08 — P2: run-report browsing bypasses the available REST read boundary

**Classification:** documented exception to retire deliberately, not an accidental
violation of the current CP-09 contract.

[cockpit/src/api/archive.ts](https://github.com/wtcross/hfcache/blob/dcc2c562b52304541d0cb85d20fc046072038e79/cockpit/src/api/archive.ts) lists and reads `/srv/hfcache/runs` using
`runuser` plus `ls`/`cat`, then parses whole JSON output. No explicit output byte
limit appears in those read functions. Its `journalForRun` also requests all
matching journal output without a retained byte/line limit in that function.
[docs/api.md](https://github.com/wtcross/hfcache/blob/dcc2c562b52304541d0cb85d20fc046072038e79/docs/api.md) already provides authenticated `GET /runs` and
`GET /runs/{run_id}` with bounded reads and exact identity checks. They are marked
SDK/HTTP, so a CLI adapter must be added rather than pretending one already exists.

**Repair:** narrow read-only `runs list` / `runs show RUN_ID` CLI commands over the
existing typed client; update the plugin to consume their documented Envelope
payloads and bounded pagination. No arbitrary path/URL/HTTP method passthrough.
Amend CP-01/09 and ADR122 when removing the exception. Keep bounded host journals
separately labeled; do not promise REST log streaming or treat journal text as an
operation result.

## F09 — P2: some read cards hide valid failed Envelopes

**Classification:** confirmed rendering defects.

[cockpit/src/verify.tsx](https://github.com/wtcross/hfcache/blob/dcc2c562b52304541d0cb85d20fc046072038e79/cockpit/src/verify.tsx) (`EstimateCard`) shows a description list after
any resolved Envelope, without `EnvelopeAlert`. [cockpit/src/dashboard.tsx](https://github.com/wtcross/hfcache/blob/dcc2c562b52304541d0cb85d20fc046072038e79/cockpit/src/dashboard.tsx)
(`VersionCard`) likewise renders scalar values but no Envelope error alert.
`runHfcache` intentionally resolves valid nonzero Envelopes, so these cards can
show dashes while suppressing an authentication, connectivity or domain refusal.

The version call itself is already `version --server`; it is not a local-version
bug. The Cockpit contract's operation table still says `version`, which should be
corrected to match the source. Status has an EnvelopeAlert and is not the same bug.
Audit every remaining consumer, rather than changing the shared runner to reject
all domain failures and breaking its existing contract.

**Repair:** consistent command-specific result rendering, failure codes preserved,
strict success payload checks and explicit stale data. Never infer “empty archive”,
“ready”, “paused” or zero estimates from an unavailable response.

## F10 — P2: copied recovery commands do not match the shipped launcher profile

**Classification:** confirmed deployment-guidance mismatch.

[cockpit/src/lib/envelope.ts](https://github.com/wtcross/hfcache/blob/dcc2c562b52304541d0cb85d20fc046072038e79/cockpit/src/lib/envelope.ts) (`operationCommands`) produces
`hfcache --json operations lookup ...` / `wait ...`. The actual adapter
[cockpit/src/lib/command.ts](https://github.com/wtcross/hfcache/blob/dcc2c562b52304541d0cb85d20fc046072038e79/cockpit/src/lib/command.ts) uses the installed rootless launcher under
the service identity, explicit client configuration and socket. The native
executable/environment implied by the copied snippets is not the selected
installation contract.

**Repair:** prefer in-page lookup/wait through the same adapter; copied commands
must use that same profile and identity without revealing a token. Preserve safe
handle grammar, `--` and argument quoting. Never observe a saved handle through a
new host, endpoint or credential-class namespace without re-establishing scope.

## F11 — P2: current gate evidence can miss the integration that failed

**Classification:** confirmed acceptance limitation, not a claim that existing
unit tests are absent or useless.

[scripts/check.sh](https://github.com/wtcross/hfcache/blob/dcc2c562b52304541d0cb85d20fc046072038e79/scripts/check.sh) explicitly skips the Cockpit gate when the toolchain
is missing. [cockpit/package.json](https://github.com/wtcross/hfcache/blob/dcc2c562b52304541d0cb85d20fc046072038e79/cockpit/package.json) defines a Node test suite and pinned
build toolchain. [docs/cockpit.md](https://github.com/wtcross/hfcache/blob/dcc2c562b52304541d0cb85d20fc046072038e79/docs/cockpit.md) and [docs/adr/decision-122.md](https://github.com/wtcross/hfcache/blob/dcc2c562b52304541d0cb85d20fc046072038e79/docs/adr/decision-122.md)
explicitly disclaim installed browser/PAM acceptance from repository tests.
The reviewed pure runner and guarded-file interfaces are useful test seams, but
those layers alone cannot establish the user's installed bridge/launcher behavior.

**Repair:** make source acceptance require an executed frontend gate plus
component lifecycle and failure-envelope regressions, CLI/socket integration, and
separately identified real Cockpit/PAM/rootless proof in a disposable environment.
Record the installed static asset, launcher/profile, image and API source identities
rather than relying on the package version string alone. No production deployment
or gate result was obtained during this review.

## Behaviors that are already aligned and must not be “fixed” away

The CLI adapter is REST-backed; ordinary commands do not pass legacy archive
`--config`; candidate calls upload TOML content. The rootless helper binds the
whole `/etc/hfcache` directory, so the candidate mount is present and atomic
replacement is visible. The explicit rootless socket differs legitimately from
the native default. Browser credentials and Hub authority remain absent. See
[cockpit/src/api/hfcache.ts](https://github.com/wtcross/hfcache/blob/dcc2c562b52304541d0cb85d20fc046072038e79/cockpit/src/api/hfcache.ts), [scripts/container-service.py](https://github.com/wtcross/hfcache/blob/dcc2c562b52304541d0cb85d20fc046072038e79/scripts/container-service.py),
[scripts/hfcache-client](https://github.com/wtcross/hfcache/blob/dcc2c562b52304541d0cb85d20fc046072038e79/scripts/hfcache-client), and [docs/api-client.md](https://github.com/wtcross/hfcache/blob/dcc2c562b52304541d0cb85d20fc046072038e79/docs/api-client.md).

The guarded configuration helper enforces bounded inert input, exact base/candidate
bytes, persistent cooperative locking, safe ownership/modes, backup and atomic
rename. The server deliberately does not install configuration. Preserve that
boundary and exact post-install confirmation:
[cockpit/src/lib/candidate-guard.ts](https://github.com/wtcross/hfcache/blob/dcc2c562b52304541d0cb85d20fc046072038e79/cockpit/src/lib/candidate-guard.ts),
[cockpit/src/lib/config-pipeline.ts](https://github.com/wtcross/hfcache/blob/dcc2c562b52304541d0cb85d20fc046072038e79/cockpit/src/lib/config-pipeline.ts), [docs/adr/decision-122.md](https://github.com/wtcross/hfcache/blob/dcc2c562b52304541d0cb85d20fc046072038e79/docs/adr/decision-122.md).

Existing Envelope schema and error-location mapping agree: backend issues carry
location in `context`, which the UI reads. Server version already uses the API.
Page detachment deliberately cannot cancel execution, and bounded progress is not
the terminal result. MCP remains separate read-only metadata access. These are
not migration bugs.

## Official Cockpit references

The documented spawn rejection fields support structured diagnosis; the docs do
not establish the cause of the user's literal `reconnected` message:
[cockpit.spawn](https://cockpit-project.org/guide/latest/cockpit-spawn.html),
[problem codes](https://docs.cockpit-project.org/cockpit-guide/latest/guide/cockpit-error.html),
[D-Bus client](https://docs.cockpit-project.org/cockpit-guide/368/guide/cockpit-dbus.html).
References were checked during this review. Use APIs supported by the actually
installed Cockpit version when implementing lifecycle handling.
