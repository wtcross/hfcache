# The hfcache Cockpit plugin

Browser administration for one deployed hfcache writer, as a
[Cockpit](https://cockpit-project.org/) package. It is static files served
by cockpit itself — no daemon, listener or independent credential backend — and a
client of surfaces the deployment already has: the CLI's `--json` envelope,
the shipped systemd units, and `/etc/hfcache/config.toml`. Every button is a
documented runbook command, and the UI names the underlying command wherever
practical, so the plugin teaches the runbook rather than hiding it.

The UI exposes the following controls. On the selected guarded rootless
installation, system-bus sync/verify/timer actions remain masked and must refuse;
CLI-based writes remain subject to the independent guard/read-only NAS. No control
redirects to identically named user units. See [deployment scope](../deployment-status.md).

From the browser you can inspect:

- watch archive health, findings, and per-repository state, and run `doctor`;
- start and observe syncs — full runs through installed services, selected
  repositories through transient API clients; stopping observation leaves accepted
  execution independent, with validated recovery handles;
- browse archived repositories and every retained revision;
- edit the configuration (form or text) through a validate-before-install
  pipeline, with exact candidate/base guards, compatible authority, required sizing
  preview and exact installed-content and operational-fingerprint confirmation;
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
and
[`docs/operations.md`](../operations.md) is the runbook every plugin action
traces back to.

Mutating anything requires an administrative Cockpit session: the plugin
escalates through Cockpit's superuser bridge and runs every CLI command as
the `hfcache` service identity — root never runs the CLI. Without
administrative access the page is read-only and says so.

Fixed privileged config/candidate/backup and retained config-lock paths are listed
in [installation](installation.md); the page adds no execution queue or archive
state store.


The fixed rootless launcher uses `/etc/hfcache/client.toml` and
`/run/hfcache/api/api.sock`. Named Podman `hfcache.api` is mounted as a protected
file inside the finite client, without host ImportCredential or a browser bearer.
Hub authority stays on the API executor. Terminal outcomes require strict bounded
schema-1 Envelopes; bounded progress/handles support display/reconnection.
The Runs tab reads reports through authenticated `runs list` / `runs show`
without a client archive mount. Optional bounded journal event diagnostics remain
host-local; journal failure does not prevent report access or establish outcome.
Repository checks do not establish browser/PAM, secret, SELinux/NFS or workload
acceptance. Native service support is separate; this plugin has no native launcher.
