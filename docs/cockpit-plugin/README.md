# The hfcache Cockpit plugin

Browser administration for one deployed hfcache writer, as a
[Cockpit](https://cockpit-project.org/) package. It is static files served
by cockpit itself — no daemon, listener or independent credential backend — and a
client of surfaces the deployment already has: the CLI's `--json` envelope,
the shipped systemd units, and `/etc/hfcache/config.toml`. Every button is a
documented runbook command, and the UI names the underlying command wherever
practical, so the plugin teaches the runbook rather than hiding it.

From the browser you can:

- watch archive health, findings, and per-repository state, and run `doctor`;
- start and observe syncs — full runs through installed services, selected
  repositories through transient API clients; stopping observation leaves accepted
  execution independent, with validated recovery handles;
- browse archived repositories and every retained revision;
- edit the configuration (form or text) through a validate-before-install
  pipeline, with exact candidate/base guards, compatible authority, required sizing
  preview and exact installed fingerprint confirmation;
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

Fixed privileged config/candidate/backup and retained config-lock paths are listed
in [installation](installation.md); the page adds no execution queue or archive
state store.


API-backed clients receive only the named encrypted API credential `hfcache.api`
through systemd and use fixed local client TOML/socket. No Hub/browser bearer
backend is added. Terminal outcomes require strict bounded schema-1 Envelopes;
bounded progress/handles support display/reconnection without invented success.
See [decision 122](../adr/decision-122.md). Repository test/build acceptance does
not establish installed systemd/credential/hardening/SELinux/NFS acceptance.
