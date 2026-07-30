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
(`0640 root:hfcache`) and every mutating control fails closed.

## A busy notice names the archive lock (`HFMNT010`)

Normal single-writer serialization, not a failure: sync, verify, prune,
repair, and recover share one lock, and the notice names the holder. A
first sync of a large repository legitimately runs for hours — check the
Sync tab's live activity. Never delete the lock file.

## The plugin refuses the CLI's output over `schema_version`

The plugin and the deployed application are out of step: the envelope's
schema is one the plugin does not know, and it refuses rather than guesses
(`CP-02`). Rebuild and reinstall the plugin from the checkout matching the
deployed release.

## Spawn errors, or an error about missing output instead of a result

The plugin invokes `/opt/hfcache/current/.venv/bin/hfcache` with
`--config /etc/hfcache/config.toml` — the runbook's deployment shape. If
the deployment moved, that path is stale. Prove the CLI works as the
service identity from a shell:

```bash
sudo runuser -u hfcache -- /opt/hfcache/current/.venv/bin/hfcache \
    --config /etc/hfcache/config.toml --json version
```

and check `install-release.sh --list` shows `current` where you expect.

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

Events appear at transaction checkpoints, not continuously — there is no
percentage to show, by design. Confirm the unit is actually running and
that the persistent journal has its `event=` lines:

```bash
systemctl is-active hfcache-sync.service
journalctl -u hfcache-sync.service -n 20
```

## A schedule override or candidate file was left behind

Both are harmless and both are removable from the UI. The override:
**Reset to shipped schedule** on the Sync tab (or remove
`/etc/systemd/system/hfcache-sync.timer.d/50-cockpit.conf` and
`systemctl daemon-reload`). A leftover `/etc/hfcache/.candidate.toml` is
inert — the service reads only `config.toml` — and **Discard candidate**
or a plain removal clears it.
