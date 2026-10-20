# hfcache Cockpit plugin

Browser administration for a deployed hfcache writer, as a
[Cockpit](https://cockpit-project.org/) package. Static files only — a
client of the fixed rootless launcher's JSON envelope, host system-bus controls, and
`/etc/hfcache/config.toml`; the application itself is untouched.

- Normative contract: [`../docs/cockpit.md`](../docs/cockpit.md)
- Install and usage: [`../docs/cockpit-plugin/`](../docs/cockpit-plugin)

Build from the repository root (node, pnpm, and make):

```bash
(
  umask 022
  make -C cockpit clean
  make -C cockpit NODE_ENV=production
)
```

Follow the [installation guide](../docs/cockpit-plugin/installation.md) for a
fresh public install, exact asset modes and readability checks. Existing packages
and per-user development shadows require inspection before replacement.

Derived from
[cockpit-project/starter-kit](https://github.com/cockpit-project/starter-kit);
this subtree is LGPL-2.1-or-later (SPDX headers per file), while the repository
as a whole is MIT.

Manual sync and verification use the fixed REST-backed CLI launcher. Original
operation keys and IDs survive tab changes and interrupted observation; recovery
looks up and observes that operation without another submission. Run reports also
use authenticated REST reads, with optional bounded host-local journal diagnostics.

The selected deployment remains guarded/read-only. Legacy system-bus writer/timer
controls are masked; no user-manager redirect is provided. Source and isolated
Cockpit/PAM acceptance do not prove the original installed symptom fixed. See the
[recorded deployment scope](../docs/deployment-status.md).
