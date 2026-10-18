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

## The page closed, timed out or stopped observing a sync

Accepted server work may continue. Preserve the validated key and operation ID
and reconnect with authenticated `operations lookup -- KEY` / `operations wait -- ID`
through the same client authority. HFAPI013 missing history and HFAPI015
interrupted/no-result state do not prove nonexecution; HFAPI019 observation and
HFAPI020 lost-ack uncertainty preserve handles. Never submit a new key or run
recovery merely because an observer stopped. For actual executor termination,
follow [server drain and supervised recovery](../recovery.md#preserve-four-kinds-of-authority).

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
Reload the installed configuration before validating another candidate; readiness
is cleared after install/confirmation failure because the rename may already have
completed. Never remove the retained config lock to force another attempt.

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
services. Report/journal browsing in the UI is host-local, not a remote REST feature.

## A schedule override or candidate file was left behind

Candidate files are inert until installed. Schedule controls remain fixed
system-manager operations and must stay blocked on the guarded deployment.
On a separately accepted system-manager integration, the override is removed by:
**Reset to shipped schedule** on the Sync tab (or remove
`/etc/systemd/system/hfcache-sync.timer.d/50-cockpit.conf` and
`systemctl daemon-reload`). A leftover `/etc/hfcache/.candidate.toml` is
inert — the service reads only `config.toml` — and **Discard candidate**
or a plain removal clears it.
