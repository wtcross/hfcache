# Recorded deployment status

Recorded on 2026-10-18 from repository evidence; this is not a fresh host
inspection.

The selected local installation is rootless 0.2.1, built from immutable
application source `4088994` on pinned UBI 10 micro. Recorded checks establish
API-container access to the confined worker under Enforcing SELinux, readiness,
verified TLS and drain/restart. Version 0.2.0 retains its API-to-worker SELinux
connection limitation when selected for rollback.

The installation remains guarded and read-only: preserve the independent host
guard, original lock inodes, read-only NAS mount, writer masks, disabled
verification calendar, both operation stores, pending scheduled observation
handles, secrets and hardening. A stopped client, free lock or wrapper exit
does not establish executor termination.

Live NAS writes, full sync/verification workloads, NFS interruption/reconnect,
consumer export isolation and copying from another host, reboot behavior,
snapshot restore, hypervisor memory reclamation, and calendar approval remain
separate acceptance work. Cockpit PAM/browser and other-host checks are also
unperformed by this documentation work. Documentation changes do not authorize
restoring write access or scheduling.

The fixed Cockpit launcher targets the rootless client and file-mounted API-only
secret. Its legacy system-bus sync/verify/timer controls remain masked; it has no
native/user-manager selector. That recorded artifact's report and journal browsers
use privileged host-local access; newer source replaces report archive reads with
authenticated REST and retains only bounded optional host journal diagnostics. Repository
plugin fixtures do not establish deployed browser/PAM or candidate-install acceptance.

The newer source routes manual full jobs through the fixed REST client and gates
effects on fresh indexed-release facts and explicit root-provisioned policy.
This is a source change, not a changed installed profile: the recorded guards,
masks, read-only mount and workload holds above remain. Older selected releases
without the required inspection artifact are unverified and fail closed.

Before a future operational window, record the exact selected artifacts, effective
system/user units and drop-ins, original lock identities, API/verifier stores,
scheduled handles, archive UUID, secret delivery and read-only guard state. A
release switch or rollback must preserve them and prove actual executor drain;
a client/wrapper exit alone is insufficient. No remote tag/publication state is
inferred by this page.
