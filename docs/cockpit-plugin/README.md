# The hfcache Cockpit plugin

Browser administration for one deployed hfcache writer, as a
[Cockpit](https://cockpit-project.org/) package. It is static files served
by cockpit itself — no daemon, no listener, no state of its own — and a
client of surfaces the deployment already has: the CLI's `--json` envelope,
the shipped systemd units, and `/etc/hfcache/config.toml`. Every button is a
documented runbook command, and the UI names the underlying command wherever
practical, so the plugin teaches the runbook rather than hiding it.

From the browser you can:

- watch archive health, findings, and per-repository state, and run `doctor`;
- start, stop, and observe syncs — full runs through the production unit,
  selected repositories as a page process — with live journal activity;
- browse archived repositories and every retained revision;
- edit the configuration (form or text) through a validate-before-install
  pipeline, with the runbook's sizing preview when adding a repository;
- change the sync schedule as a managed systemd drop-in;
- verify — an estimate, one revision, or the full offline read;
- read durable run reports joined to their journal trails;
- prune, recover, and repair, dry-run first.

Deliberately outside the plugin, by contract: initializing archives,
enabling the quarterly verification timer, touching `hfcache.target`, any
credential entry, and any host other than the one it is installed on
([`docs/cockpit.md`](../cockpit.md) §10).

| Document | Contents |
| --- | --- |
| [`installation.md`](installation.md) | Requirements, build, install, update, remove |
| [`usage.md`](usage.md) | Every tab and flow, and how to read the plugin's alerts |
| [`troubleshooting.md`](troubleshooting.md) | Symptoms, causes, fixes |

[`docs/cockpit.md`](../cockpit.md) is the plugin's normative contract
(`CP-01`–`CP-14`) — what it must and must never do; these pages are the
operator guide written against it. The writer host itself is built by
[`docs/deployment-centos-stream-10.md`](../deployment-centos-stream-10.md)
(§16 is the deployment-step summary of the installation guide here), and
[`docs/operations.md`](../operations.md) is the runbook every plugin action
traces back to.

Mutating anything requires an administrative Cockpit session: the plugin
escalates through Cockpit's superuser bridge and runs every CLI command as
the `hfcache` service identity — root never runs the CLI. Without
administrative access the page is read-only and says so.
