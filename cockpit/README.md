# hfcache Cockpit plugin

Browser administration for a deployed hfcache writer, as a
[Cockpit](https://cockpit-project.org/) package. Static files only — a
client of the CLI's JSON envelope, the shipped systemd units, and
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
this subtree is LGPL-2.1-or-later (SPDX headers per file; decision 90 in
`../docs/progress.md`), while the repository as a whole is MIT.
