# Installing the Cockpit plugin

## What gets installed

`/usr/share/cockpit/hfcache` — static HTML, JavaScript, and CSS plus
`manifest.json`, root-owned, served by cockpit's own web service. Nothing
else: no unit, no daemon, and no addition to the application's runtime
dependency set (`CP-14`).

Two further pieces of host state exist only after you use the features that
manage them, and both are removable from the UI:

| Path | Created by | Removed by |
| --- | --- | --- |
| `/etc/systemd/system/hfcache-sync.timer.d/50-cockpit.conf` | The schedule override (Sync tab) | "Reset to shipped schedule" |
| `/etc/hfcache/.candidate.toml` | The configuration editor, mid-pipeline | "Discard candidate", or installing it |
| `/etc/hfcache/config.toml.bak` | Installing a configuration | Kept deliberately — the one retained predecessor |

## Requirements

On the host that will serve the plugin:

- an hfcache deployment in the runbook's shape —
  `/opt/hfcache/current/.venv/bin/hfcache`, `/etc/hfcache/config.toml`, and
  the shipped units ([`deployment-centos-stream-10.md`](../deployment-centos-stream-10.md));
  the plugin invokes exactly those paths;
- `cockpit` ≥ 137 with its socket enabled
  (`systemctl enable --now cockpit.socket`); the reference deployment runs
  cockpit 364.

On the machine that builds it (the same host, or any other):

- node `^24.18.1` and pnpm ≥ 11 (`cockpit/package.json` pins
  `pnpm@11.18.0`). The Makefile finds pnpm on `PATH` or falls back to
  `$PNPM_HOME/bin` (`~/.local/share/pnpm` by default) and puts node beside
  it on recipe `PATH`, so a non-login shell works. A different location:
  `make PNPM=/path/to/pnpm …`;
- `make` and `git`;
- network access, first build only: the package registry for the frozen
  `pnpm install`, and github.com to fetch Cockpit's `pkg/lib` at the commit
  the Makefile pins.

## Build and install

From the repository root:

```bash
make -C cockpit clean                  # drop any previous (development) build
make -C cockpit NODE_ENV=production    # minified, precompressed bundles in cockpit/dist/
sudo make -C cockpit install           # copy to /usr/share/cockpit/hfcache
```

`NODE_ENV=production` matters: `install` copies whatever `dist/` holds, and
without it the build is an unminified development bundle — functional, just
larger. `clean` first, because make considers an existing development build
up to date.

Verify, then use:

```bash
cockpit-bridge --packages | grep hfcache
```

and in the browser: log in to Cockpit (`https://<writer-host>:9090`) and
open **Tools → hfcache**. Cockpit reads the package list at login — log out
and back in if the entry does not appear.

## Building on one machine, installing on another

`dist/` is portable static files. Build anywhere the toolchain lives, then
copy to the writer:

```bash
sudo mkdir -p /usr/share/cockpit/hfcache
sudo cp -r cockpit/dist/* /usr/share/cockpit/hfcache/
```

This is the path for a writer without node — the toolchain is build-time
only, deliberately (`CP-14`).

## Development loop

```bash
make -C cockpit devel-install     # symlink dist/ as ~/.local/share/cockpit/hfcache
make -C cockpit watch             # rebuild on change; refresh the browser
make -C cockpit devel-uninstall   # remove the symlink
```

The per-user symlink **shadows** the system copy for that user: while it
exists, that account sees the development build regardless of what
`/usr/share/cockpit/hfcache` holds.

## Updating

Pull, rebuild, reinstall — the same three commands as the install. Files
are replaced in place; a browser refresh picks them up. Keep the plugin and
the deployed application in step: the plugin refuses a JSON envelope whose
`schema_version` it does not know, rather than guessing (`CP-02`).

## Removing

```bash
sudo rm -rf /usr/share/cockpit/hfcache
make -C cockpit devel-uninstall    # where the development symlink was used
```

The managed state in the table above survives removal by design — a
schedule override keeps working without the plugin. To retire that too:
reset the schedule from the UI first (or remove the drop-in and run
`systemctl daemon-reload`), and delete a leftover
`/etc/hfcache/.candidate.toml`. Leave `config.toml.bak` unless you are sure
you do not want the predecessor.
