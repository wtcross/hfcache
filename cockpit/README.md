# hfcache Cockpit plugin

Browser administration for a deployed hfcache writer, as a
[Cockpit](https://cockpit-project.org/) package. Static files only — a
client of the fixed rootless launcher's JSON envelope, host system-bus controls, and
`/etc/hfcache/config.toml`; the application itself is untouched.

- Normative contract: [`../docs/cockpit.md`](../docs/cockpit.md)
- Install and usage: [`../docs/cockpit-plugin/`](../docs/cockpit-plugin)

Build and install (node, pnpm, and make — see the installation guide):

```bash
make clean && make NODE_ENV=production
sudo make install                 # → /usr/share/cockpit/hfcache
```

Derived from
[cockpit-project/starter-kit](https://github.com/cockpit-project/starter-kit);
this subtree is LGPL-2.1-or-later (SPDX headers per file), while the repository
as a whole is MIT.

The selected deployment remains guarded/read-only. Legacy system-bus writer/timer
controls are masked; no user-manager redirect is provided. The report browser is
a host-local `runuser` + `ls`/`cat` exception requiring the writer archive mount,
separate from API-backed metadata commands. See the
[recorded deployment scope](../docs/deployment-status.md).
