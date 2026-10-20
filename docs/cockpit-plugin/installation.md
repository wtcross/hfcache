# Installing the Cockpit plugin

## What gets installed

`/usr/share/cockpit/hfcache` — static HTML, JavaScript, and CSS plus
`manifest.json`, root-owned, served by cockpit's own web service. Nothing
else: no unit, no daemon, and no addition to the application's runtime
dependency set (`CP-14`).

The plugin manages these fixed host paths after their features are used:

| Path | Created by | Removed by |
| --- | --- | --- |
| `/etc/systemd/system/hfcache-sync.timer.d/50-cockpit.conf` | The schedule override (Sync tab) | "Reset to shipped schedule" |
| `/etc/hfcache/.candidate.toml` | The configuration editor, mid-pipeline | "Discard candidate", or installing it |
| `/etc/hfcache/config.toml.bak` | Installing a configuration | Kept deliberately — the one retained predecessor |
| `/etc/hfcache/.configuration.lock` | Guarded configuration pipeline | Retained; never unlink to bypass locking |

These are guarded operations, not a cleanup list. After an uncertain write or
installation, retain the candidate, backup, original lock and displayed cause.
Use explicit read-only inspection and authenticated original-operation recovery;
do not delete a candidate or repeat Apply to make an alert disappear.

## Requirements

On the writer host serving the plugin:

- the selected rootless deployment's fixed `/usr/local/libexec/hfcache-client`
  wrapper and protected runtime profile, plus `/etc/hfcache/config.toml`;
- `/etc/hfcache/client.toml`, `0640 root:hfcache`, selecting
  `/run/hfcache/api/api.sock` and the mounted API-only file source. The effective
  content is the physical release's `rendered/client.toml`, overlaid at that path
  inside the client. Review the [client template](../../packaging/containers/client.toml)
  and any expected-archive UUID pin before authenticating/rendering the release;
  editing the host placeholder does not change the effective settings. Retain the
  protected release binding;
- a separately provisioned named Podman `hfcache.api` secret for REST writer
  authority. The wrapper mounts it only inside the finite client; no host
  `ImportCredential`, browser bearer or Hub secret is involved;
- Cockpit at least 137 with separately approved socket/authentication setup.

The shipped launcher has no native profile selector. Native systemd credential/
socket examples in the server guide are separate integration requirements, not
instructions for this rootless plugin. The selected system-bus writer/timer units
stay masked; administrative access cannot make those controls accepted workloads.
The report browser uses authenticated `runs list` / `runs show` through the same
fixed client and needs no client archive mount. Optional journal diagnostics
remain host-local and may be unavailable independently of reports. See the
[contract](../cockpit.md) and [recorded restrictions](../deployment-status.md).

Compare the loaded browser build-input identity, selected protected release
source/index/image and authenticated client/API identity independently. A dirty
or unknown browser build cannot establish source parity. The input digest covers
declared public build inputs and lock/pin files; it is not the output bundle
checksum or a hash of installed dependency bytes. Selected bindings do not prove
which payload is currently running. Keep exact bundle checksums and active image
verification in the operator rollout record; package version alone is insufficient.
Source provenance currently requires Linux descriptor-anchored public input reads.
Other build platforms, development and watch builds report unknown provenance;
they do not substitute an unguarded input scan.

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
(
  umask 022
  make -C cockpit clean
  make -C cockpit NODE_ENV=production
)
```

`NODE_ENV=production` matters: `install` copies whatever `dist/` holds, and
without it the build is an unminified development bundle — functional, just
larger. `clean` first, because make considers an existing development build
up to date.

For a **fresh** system package, first confirm that the target is absent, including
a dangling symlink, then install with the public-file umask:

```bash
sudo sh -eu -c '
  umask 022
  test ! -e /usr/share/cockpit/hfcache
  test ! -L /usr/share/cockpit/hfcache
  make -C cockpit NODE_ENV=production install
'
```

An existing target requires the [update inspection](#updating) below. `make
install` copies the build and inherits its modes and the installer's umask; it
does not repair a package built or installed under `umask 077`.

The production package has exactly these five known regular public assets:
`manifest.json`, `index.html`, `index.js.gz`, `index.css.gz` and
`index.js.LEGAL.txt`. Inspect the destination and every asset:

```bash
stat -c '%F %U:%G %a %n' /usr/share/cockpit/hfcache \
  /usr/share/cockpit/hfcache/manifest.json \
  /usr/share/cockpit/hfcache/index.html \
  /usr/share/cockpit/hfcache/index.js.gz \
  /usr/share/cockpit/hfcache/index.css.gz \
  /usr/share/cockpit/hfcache/index.js.LEGAL.txt
namei -l /usr/share/cockpit/hfcache/manifest.json
```

Expect a `root:root` `0755` package directory, `root:root` `0644` regular files and
searchable parent directories. Confirm that both the actual Cockpit login account
and the `hfcache` service identity can traverse and read these public files. For
each account, run the following with `ACCOUNT` replaced by its name:

```bash
sudo -u ACCOUNT test -x /usr/share/cockpit/hfcache
sudo -u ACCOUNT cat \
  /usr/share/cockpit/hfcache/manifest.json \
  /usr/share/cockpit/hfcache/index.html \
  /usr/share/cockpit/hfcache/index.js.gz \
  /usr/share/cockpit/hfcache/index.css.gz \
  /usr/share/cockpit/hfcache/index.js.LEGAL.txt >/dev/null
```

These checks establish file readability, not successful PAM, privilege transition
or SELinux execution. If modes are wrong, first verify the exact known directory,
regular assets and source hashes; correct only those public assets to the modes
above. Do not use recursive permission changes, widen private configuration or
credential directories, or alter unknown files to make package discovery work.

In the actual login user's session, inspect `cockpit-bridge --packages` for the
selected `hfcache` package path. Then log in to Cockpit
(`https://<writer-host>:9090`) and open **Tools → hfcache**. Cockpit reads the
package list at login; log out and back in after a discovery change. Inspect
per-user shadows before assuming that this selected package is the system copy.

## Building on one machine, installing on another

`dist/` is portable static files. Build anywhere the toolchain lives, then
transfer the five verified assets to the writer. For a fresh destination, install
only those assets with explicit public modes:

```bash
sudo sh -eu -c '
  umask 022
  test ! -e /usr/share/cockpit/hfcache
  test ! -L /usr/share/cockpit/hfcache
  install -d -o root -g root -m 0755 /usr/share/cockpit/hfcache
  install -o root -g root -m 0644 \
    cockpit/dist/manifest.json cockpit/dist/index.html \
    cockpit/dist/index.js.gz cockpit/dist/index.css.gz \
    cockpit/dist/index.js.LEGAL.txt /usr/share/cockpit/hfcache/
'
```

This is the path for a writer without node — the toolchain is build-time
only, deliberately (`CP-14`). Compare transferred hashes with the build record,
then perform the same destination-mode, account-readability and package-path
checks above.

## Development loop

```bash
make -C cockpit devel-install     # symlink dist/ as ~/.local/share/cockpit/hfcache
make -C cockpit watch             # rebuild on change; refresh the browser
make -C cockpit devel-uninstall   # remove the symlink
```

The per-user symlink **shadows** the system copy for that user: while it
exists, that account sees the development build regardless of what
`/usr/share/cockpit/hfcache` holds. Inspect its type and target before using
`devel-uninstall`; an unrelated real directory or symlink must not be replaced or
removed. Also inspect the user's configured XDG data path when package discovery
selects a different location.

## Updating

Record the current selected package path, exact asset hashes and modes before
replacement. Preserve a reviewed copy of the known public assets. Verify that
the destination and each of the five names above have the expected owner and
regular-file type; stop on unexpected files, symlinks or contents. Rebuild under
`umask 022`, then replace only the reviewed public assets with `0644` root-owned
files and retain the `0755` directory. Preserve unrelated files and all private
configuration, backups, locks and operation evidence.

Log out and back in after package discovery changes, and reload the page to load
the selected assets. A hard reload can refresh cached bytes; it cannot correct a
per-user package shadow or prove which build was loaded. Do not clear session
storage as a cache remedy: it holds original-operation recovery metadata. Compare
the loaded diagnostic identities with the rollout record and verify the exact
served bundle checksum independently. For production JavaScript, distinguish the
compressed `index.js.gz` file hash from the decompressed bundle hash; record which
one was compared. Equal package versions do not prove equal source, browser
bundles, selected images or running processes.

Keep the plugin and deployed application in step: the plugin refuses an unknown
Envelope `schema_version` rather than guessing (`CP-02`). See
[troubleshooting](troubleshooting.md) for identity and reconnect diagnosis. An
update never authorizes replay, installation, rollback or cleanup after uncertain
execution.

## Removing

Before removal, preserve original operation keys, IDs and authority scope and any
uncertain configuration or schedule evidence. Inspect the selected package and
remove only the five verified public regular files listed above; remove the
package directory with `rmdir` only when it is empty. Preserve and investigate
unexpected files or symlinks. For a development package, `make -C cockpit
devel-uninstall` applies only after confirming the known development symlink and
its target.

The managed state in the table above survives removal by design. A schedule
override keeps working, and accepted API execution continues independently.
Retiring a schedule or candidate is a separate deliberate operation after its
state is reconciled; removal is not permission to reset, delete, reload, rollback
or cancel after an uncertain response. Keep the backup and persistent
`.configuration.lock` inode, plus operation and scheduled history. Never delete a
leftover candidate merely because the browser package is being removed.

## Acceptance boundary

Repository acceptance runs Cockpit lint/style/type/tests and production build
through `make -C cockpit check` and `scripts/check.sh --require-cockpit`; a skipped
frontend stage is not passing plugin evidence. Injected process/config fixtures
test failed and uncertain results, bounded streams, page detachment and exact
candidate/base guards without changing the host's units or archive.

Separate current-artifact disposable acceptance exercised real Cockpit/PAM and
privileged bridge transitions, the fixed rootless client, authenticated API calls,
exact candidate installation/confirmation and read-only inspection after bridge
interruption, retaining SELinux enforcement and archive guards. This does not
establish parity with the recorded installed artifact, resolve its original
symptom, accept live NAS/workloads or authorize deployment. Repository checks do
not perform a host installation. Preserve earlier uncertain attempts even when a
fresh disposable test passes.
