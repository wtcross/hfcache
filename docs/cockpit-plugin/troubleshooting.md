# Troubleshooting the Cockpit plugin

Symptoms in the order you are likely to meet them. Where a fix involves the
application rather than the plugin, [`operations.md`](../operations.md) and
[`recovery.md`](../recovery.md) take over.

## The menu has no hfcache entry

Cockpit reads the package list at login — log out and back in first. Then
confirm the package is visible to the bridge:

```bash
cockpit-bridge --packages | grep hfcache
```

Nothing listed means `/usr/share/cockpit/hfcache/manifest.json` is missing
or unreadable, or cockpit is older than 137 (the manifest's `requires`).

## The page shows a different build than the one installed

A development symlink at `~/.local/share/cockpit/hfcache` shadows the
system copy for that user. `make -C cockpit devel-uninstall` removes it.

## Everything is read-only, or actions fail with permission errors

Administrative access is off. Turn it on in Cockpit's top bar; the account
must be an administrator (`wheel`). This is the designed degraded state:
without the superuser bridge the configuration is unreadable
(`0640 root:hfcache`) and every mutating control fails closed. Even with administrative access,
the selected guard/read-only mount and masked system units remain restrictions,
not permission failures to bypass.

## A busy notice names the archive lock (`HFMNT010`)

Normal single-writer serialization, not a failure: sync, verify, prune, purge,
repair, and recover share one lock, and the notice names the holder. A
first sync of a large repository legitimately runs for hours — check the
Sync tab's live activity. Never delete the lock file. The permanent read-only guard can intentionally
hold it; waiting does not authorize releasing that guard.

## The plugin refuses the CLI's output over `schema_version`

The plugin and the deployed application are out of step: the envelope's
schema is one the plugin does not know, and it refuses rather than guesses
(`CP-02`). Rebuild and reinstall the plugin from the checkout matching the
deployed release.

## Spawn errors, or an error about missing output instead of a result

The shipped plugin uses the fixed rootless launcher in a service-identity
transient unit. Ordinary commands omit archive `--config`. In an accepted local
connection window, reproduce the same bounded client/server version request:

```bash
sudo systemd-run --quiet --wait --pipe --collect \
    -p User=hfcache -p Group=hfcache -p UMask=0027 -p MemoryHigh=4G \
    -- /usr/local/libexec/hfcache-client \
    --client-config /etc/hfcache/client.toml \
    --api-socket /run/hfcache/api/api.sock --json version --server
```

Check the protected release/profile binding and its effective rendered client
settings (not just the host placeholder), then the named
Podman `hfcache.api` source. No host `ImportCredential` applies. Missing API source
is HFAPI003; invalid/wrong-interface bearer is HFAPI001 and insufficient class is
HFAPI002. Never put a bearer/Hub token in argv/environment or weaken SELinux.
Hub authority remains on the API executor. Use the container installer for this
profile; the native installer deliberately refuses it. An unsuitable output-file
label can cause a pipe redirection denial; diagnose the label under the deployment
contract, preserving enforcement.

The plugin refuses malformed, unknown-version or oversized terminal output and
retains bounded diagnostics/validated handles instead of inventing success.

## A host action reports `reconnected`

Read cards preserve original failed CLI codes before displaying payload data.
Empty-success captions require validated successful reads. A failed refresh clears
prior current evidence; partial data stays informational. Unreachable status does
not imply zero unfinished work or healthy capacity. A malformed payload is a
separate observation refusal and never makes a control ready.

Use **Source and connection diagnostics** to compare the loaded browser build, selected
physical release and authenticated client/API target. A missing or dirty build,
stale profile, changed API instance or source mismatch requires review. The browser
build-input digest is not an output checksum; selected bindings are not proof of
the active payload. Keep exact installed checksums/image/process identities in
the operator record. Do not repair a native default socket or import a local
binary merely because the protected rootless overlay selects a different endpoint.

The error identifies the interrupted stage and validated Cockpit problem/process
facts. `reconnected` indicates a bridge/session transition, not an established
API crash. Distinguish it from a launcher/process start failure, a classified
HFAPI failure Envelope and a failed domain result. Unknown rejection prose and raw
host stderr are withheld to avoid disclosing credentials or configuration.

Read connections are recreated with a finite retry budget. Failed polls clear
healthy-looking evidence, and administrative changes disable dependent controls
until fresh reads. The page does not repeat a unit change, schedule write,
candidate pipeline or job. After an interrupted host write/install, preserve the
candidate/base/backup and use guarded read-only comparison before another change.
After an uncertain job, preserve its original key/ID and use authenticated
lookup/wait. A synchronous validation has no operation receipt. Actual installed
trigger diagnosis still requires checking the exact browser/helper/profile/image
identities in an authorized environment; changing error text alone proves no fix.

Older guarded configuration code sent NUL-delimited documents through a Cockpit
text channel. Independent read-only tests with Cockpit368 reproduced a real
bridge disconnect for that input, including privileged channels. The repaired
guard sends bounded canonical ASCII base64 frames and validates both exact UTF-8
documents before file or lock effects. This identifies a reproducible transport
defect, without establishing the cause on another installed host. Verify the
actual browser source/checksum and selected helper/profile before an authorized
installed test. Preserve any earlier uncertain attempt; another Validate click
is not a diagnostic read.

Installed confirmation must keep systemd's stdout on a pipe. Redirecting it
straight into the root confirmation file can produce an enforcing PID1 `init_t`
write denial on an `etc_t` file before a client unit starts. The repaired guard
uses a bounded local privileged collector and exact byte postchecks. Preserve
an already installed file, backup and failed confirmation; do not relabel files,
weaken SELinux or repeat installation to resolve that observation.

## The page closed, timed out or stopped observing a sync

Accepted server work may continue. Preserve the validated key and operation ID
and reconnect with authenticated `operations lookup -- KEY` / `operations wait -- ID`
through the same client authority. HFAPI013 missing history and HFAPI015
interrupted/no-result state do not prove nonexecution; HFAPI019 observation and
HFAPI020 lost-ack uncertainty preserve handles. Never submit a new key or run
recovery merely because an observer stopped. For actual executor termination,
follow [server drain and supervised recovery](../recovery.md#preserve-four-kinds-of-authority).

Use **Original operations**, which remains outside tab lifetime and restores safe
records from this browser tab's session storage after reload. Look up the saved
key, then observe its original ID. The copied commands retain the fixed launcher,
service identity, client settings/socket and expected authority pin; quoted keys
follow `--`. Never paste a key into a new submission or interpret a leading `-`
or `~` as a command option or shell expansion.

## Original operations reports unavailable storage or changed authority

Session recovery accepts at most 32 records and 64 KiB of strictly validated
metadata. Missing browser access, quota/write failure, corruption or an unresolved
record blocks additional keyed submissions. Preserve displayed keys/IDs and the
original storage evidence. Clearing storage is not evidence that execution ended.
Unresolved records are not evicted to make room; conclusive terminal summaries
may be evicted only when capacity requires room for another submission.
After reload, even a well-shaped terminal summary is unverified. Confirm the
original authenticated result before another submission. A contradictory result
or unavailable/expired history preserves the record for review; changing its
stored state to success does not establish execution outcome.

Refresh client authority through the fixed authenticated client. `client describe`
reports only allowlisted nonsecret metadata; a metadata/credential-literal
collision refuses with `HFAPI017` rather than publishing a damaged authority pin.
A failed capabilities/version request retains its original classified Envelope.
An unconfirmed archive UUID stays null and blocks submission/saved observation.
Changed host/profile/endpoint/credential class/archive identity blocks following
the old handle through the new authority. Preserve both identities for review;
do not edit saved metadata to force a match. The same-process
`--expected-client-scope` check refuses a changed target before the requested
submission or lookup/wait. No endpoint is selected from browser storage.

## A successful maintenance dry run no longer enables Apply

Apply requires that preview's authority and administrative connection to remain
current. Refreshing authority or reconnecting can invalidate old readiness.
After an Apply submit/observation error, the preview stays consumed even if no
applied Envelope arrived. Use the original-operation controls to resolve the
original work; another click, tab change or missing-history response is not
permission for another POST. Configuration confirmation and acknowledgement also
refuse stale or changed authority while retaining the original draft and failure.

## Candidate validity succeeds but install stays disabled

Syntax validity is separate from installed-authority compatibility and preview
readiness. Incompatible or unknown authority requires manual privileged review/
install/backup, any required daemon restart, then compatible validation/preview.
The page never sends daemon credentials to proposed endpoints or credential
sources. Failed required preview leaves install disabled. Editing either candidate
or installed base invalidates prior evidence: reload/revalidate rather than
bypass `/etc/hfcache/.configuration.lock` or replace it.

If installed confirmation fails or its fingerprint differs, installation is
unconfirmed. Retain the backup and evidence, inspect installed API validation,
and follow the operator runbook; do not assume the previous file still exists,
show success or silently roll back.
Use **Inspect captured configuration** for read-only exact comparisons. A matching
candidate/base permits explicit revalidation without another write. An uncertain
installation requires matching installed bytes and retained predecessor, explicit
confirmation through the API and acknowledgement before a fresh preparation.
Keep the original classified error; inspection/confirmation errors are additional
evidence. Absent, changed or unknown files do not prove nonexecution. A reload or
tab change cannot clear uncertainty, and a new page cannot claim an old candidate.
Never remove the retained config lock to force another attempt.

## Build fails: `pnpm: command not found` or `node: command not found`

pnpm lives in `PNPM_HOME` (`~/.local/share/pnpm` by default), which is on
login-shell `PATH` only. The Makefile resolves that location by itself and
exports node beside it; from elsewhere, point it explicitly:
`make -C cockpit PNPM=/path/to/pnpm`.

## Build fails fetching `pkg/lib`

The first build fetches Cockpit's `pkg/lib` from github.com at a pinned
commit; it needs network once, then lives in `cockpit/pkg/` (`make clean`
keeps it; `make distclean` removes it).

## `pnpm install` rejects the lockfile

Installs are frozen deliberately — the committed `pnpm-lock.yaml` is the
build. A mismatch means `package.json` changed without its lockfile; build
from a clean checkout rather than updating dependencies to get past it.

## The live activity feed shows nothing during a run

The client reports only bounded operation events actually emitted by the API;
there may be no per-repository checkpoint or byte percentage. Retention gaps and
dropped oversized lines are explicit. Unit activity/journal diagnostics do not
prove terminal outcome. Inspect the observer and preserve its recovery handles:

```bash
systemctl is-active hfcache-sync.service
journalctl -u hfcache-sync.service -n 20
```

These system-manager commands inspect the legacy observer; they do not inspect
the rootless API/worker payload. Use the selected user-manager lifecycle for those
services. Report browsing uses authenticated REST; only optional bounded journal
diagnostics are host-local. Missing journal events do not make a report absent or
establish success/failure. Stale report cursors require an explicit first-page
refresh; missing/corrupt/wrong-identity reports retain classified errors with no
direct archive-file fallback.

## A schedule override or candidate file was left behind

Candidate files are inert until installed. Schedule controls remain fixed
system-manager operations and must stay blocked on the guarded deployment.
On a separately accepted system-manager integration, the override is removed by:
**Reset to shipped schedule** on the Sync tab (or remove
`/etc/systemd/system/hfcache-sync.timer.d/50-cockpit.conf` and
`systemctl daemon-reload`). A leftover `/etc/hfcache/.candidate.toml` is
inert — the service reads only `config.toml`. **Discard candidate** is available
only for an acknowledged, owned exact candidate/base. It refuses after uncertain
execution or changed ownership. Preserve unknown files and backups for explicit
operator review; their names alone never authorize removal.

## Tags and installed confirmation

Tags are comma-separated flat labels. Invalid characters, empty elements or
oversized lists must be fixed before form serialization; text mode can submit a
candidate to authoritative backend validation. Existing configured tags supply
suggestions without a registry. Tags never choose files or grant access.

A tag-only external edit leaves the operational fingerprint unchanged but changes
the document. Exact candidate/base checks and installed confirmation refuse that
conflict. Reload the installed document and validate the intended draft again;
never retry an uncertain install automatically or overwrite the other editor's
labels. The retained backup and configuration lock remain evidence.

Source/component checks, disposable runtime checks and installed-host diagnosis
are separate evidence. The isolated launcher fixture's successful version and
candidate validation used an older immutable application artifact; they do not
validate newer authority/recovery code or prove the original installed
`reconnected` cause. Actual Cockpit/PAM/session acceptance and guarded deployment
verification still require their recorded environment and artifact prerequisites.
