# Recorded deployment status

Recorded on 2026-10-20 after the local rootless 0.2.2 deployment and installed
acceptance. The selected release uses clean application source `1c68501` on
pinned UBI 10 micro, app image `fec39364…`, unchanged Caddy image `fa2a5634…`,
and artifact index `bc40f9d7…`. All 64 indexed files and the nine protected
through-current bindings were verified. The local annotated `v0.2.2` tag targets
that exact application source; no remote tag publication is inferred here.

Actual installed acceptance verified TLS and thirteen HTTP authentication/MCP
cases, including credential separation and all fourteen MCP tools. Separate
checks proved API-container access to the confined worker, notification readiness,
and the fixed host CLI reporting version 0.2.2. Actual PID1 checks establish credential masks, zero
capabilities, no new privileges, seccomp mode and a read-only root under Enforcing
SELinux.
IP-socket denial remains separately proved by the indexed worker fixture; a
`podman exec` probe does not establish PID1 seccomp behavior.

The installation remains guarded and read-only: preserve the independent host
guard, original lock inodes, read-only NAS mount, writer masks, disabled
verification calendar, operation stores, scheduled observation handles, secrets
and hardening. Guard PID `1868228` owns the original domain lock, device/inode
`27:2273`. The six retained control-store files, existing configuration,
candidate, backup, lock identities, and secret identities and bytes were
unchanged. Protected backup and rollout evidence are retained at
`/opt/hfcache/deployment/20261020-cockpit-0.2.2`.

The original Timestral operation was observed through its original identity;
its terminal `HFMNT010` failure result remains byte-identical (`9c0b18f8…`) and
was never replayed. A stopped client, free lock or wrapper exit does not establish
executor termination.

Live NAS writes, full sync/verification workloads, NFS interruption/reconnect,
consumer export isolation and copying from another host, reboot behavior,
snapshot restore, hypervisor memory reclamation, and calendar approval remain
separate acceptance work. Source, fixture and installed metadata checks do not
establish those behaviors or authorize restoring write access or scheduling.

The fixed Cockpit launcher targets the rootless client and file-mounted API-only
secret. Its legacy system-bus sync/verify/timer controls remain masked; it has no
native/user-manager selector. The installed plugin now reads reports through
authenticated REST, retains bounded optional host journal diagnostics, and routes
manual full jobs through the fixed REST client. Effects require fresh indexed
release facts and explicit root-provisioned policy. Only configuration permission
is enabled; archive, Hub, control, schedule and observer permissions remain denied.
The existing workload holds remain in force.

Production Cockpit PAM/browser and candidate-install acceptance remain unperformed.
The next operator verification is a fresh browser reload and read-only inspection
of the preserved candidate. Do not overwrite, reinstall, discard or clean up that
candidate to test the rollout. No original installed `reconnected` cause or browser
symptom correction is claimed.

Source and disposable acceptance recorded on 2026-10-20 repair classified errors,
original-operation retention, candidate readiness/reconciliation, manual REST jobs
and report/read presentation. Actual isolated runtime probes reproduced and
corrected timer-property inspection, NUL-framed Cockpit text input and PID1 output
redirection under Enforcing SELinux. Real private-socket tests also proved the
Unix HTTP empty-write ownership correction. A fresh disposable Cockpit/PAM/rootless
test passed exact candidate API validation, installation and confirmation, followed
by bridge interruption and read-only captured-byte inspection. Installed-wheel
tests establish the CLI/API boundary separately from browser acceptance.

This disposable evidence uses synthetic archives without production credentials
or a live/NAS archive. The five retained guest environments include earlier
unknown candidate execution and unconfirmed installation; later fixture success
does not authorize their retry, rollback or cleanup.

During rollout, an inappropriate static user-unit verification against the live
runtime replaced the manager's private socket. An isolated reproduction and
source inspection established that separate cause. The endpoint was restored
only after authenticated API-first drain and complete executor quiescence; no
operation was replayed. Future static verification must use independently owned
runtime, bus and generator paths. This incident does not explain the original
Cockpit symptom.

Immutable 0.2.1, source `4088994`, remains retained as the predecessor. Selecting
0.2.0 for rollback returns its API-to-worker SELinux connection limitation.
Any future switch or rollback must preserve configuration, candidates, stores,
handles, secrets, original locks and barriers, with actual executor drain proved
before selection. Reboot, NAS, export and other-host acceptance remain outstanding.
