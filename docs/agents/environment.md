# Working near a live archive

For coding agents whose checkout may be on a production writer. Determine the
host and mount before any work outside the repository:

```bash
hostname
findmnt /srv/hfcache
```

Treat an existing archive as live. Repository implementation does not authorize
host operations, deployment, archive jobs, NAS changes or schedule enablement.
Determine current installed state from protected host configuration and the
operator's execution context; repository history is not current authorization.

## Hard limits

- Never write under `/srv/hfcache` outside the application's transactional code
  paths: no manual creation, deletion, chmod, relabel or repair.
- Never run `hfcache archive init` against the existing archive. Its sentinel
  and configured UUID establish identity.
- Never weaken SELinux, systemd confinement, credential separation or file
  permissions to make a check pass. Keep SELinux enforcing.
- No reboots, network-stack or `remote-fs.target` restarts, live mount
  disconnections or NAS-side changes as repository tests.
- Do not enable verification or sync calendars without explicit operator scope.
  Pause individual timers during approved deployment; do not stop
  `hfcache.target` to quiesce the archive.
- Preserve original lock inodes, both operation stores, scheduled observation
  handles, candidate/backup files and original credential identities.
  Stopping a client or finding a free lock does not prove executor termination.
- Build and test as the login user. Root installation/configuration work needs
  an explicitly authorized deployment scope. Use owned fixtures and the
  disposable archive procedure in [recovery](../recovery.md), never the live
  archive, for mutable rehearsals.

## Profile and manager boundaries

Native services use the system manager and a host release interpreter.
Rootless API, worker and Caddy use the service account's user manager; the
protected host helper, system bridge and independent guard are distinct controls.
The fixed host client is `/usr/local/libexec/hfcache-client`; image execution
uses `/opt/hfcache/.venv/bin/hfcache`. Follow the selected profile in
[deployment](../deployment-centos-stream-10.md) and [containers](../containers.md).
Never run the native installer against an unknown, mixed or container layout.

Protected Podman credentials are file mounts with separate REST, MCP and Hub
sources. The client receives REST only and the verifier receives none. Do not
print secret values. Prove actual API/worker/helper and container/cgroup drain
before switching artifacts or transferring an original guard lock. Unknown
activity refuses further work; no forced cleanup, replay or automatic rollback.

A guarded rootless profile requires independently proven host read-only storage,
writer masks and READY guard ownership; a private read-only mount view is not
host proof. Writer mode needs separately protected authority. Preserve the
selected profile and existing calendar restrictions through a switch.

Never run `systemd-analyze --user verify` with a live `XDG_RUNTIME_DIR`.
Use owned isolated runtime, bus and unit/generator paths as described in
[static verification](../containers.md#static-user-unit-verification).
Preserve a stale endpoint for review rather than unlinking it or restarting
its manager blindly. Persistent labels alone do not establish startup ordering
or unattended boot support. Provision runtime parents and establish helper READY
before bridge/API startup according to the selected deployment procedure.
