# Preserve a dedicated rootless archive-lock label for metadata-only guard proof

- Decision identity: 159.
- Status: Accepted; installed conformance remains separately required.
- Date: 2026-10-29.
- Introducing change: this commit.

## Context and decision

The installed rootless API and worker share the original local archive lock.
Their ordinary shared bind relabels that file to `container_file_t`. The confined
host helper's fixed mixed-ID guard observer then cannot stat the lock. Granting
the helper access to generic container payload types would weaken the existing
payload boundary merely to inspect one coordination object.

For explicit rootless host-helper enablement, independently provision
`hfcache_host_helper_archive_lock_t` on exactly the existing
`/run/hfcache/hfcache.lock`. Preserve its device/inode, service UID/GID,0600 mode
and single link. The helper receives only file `getattr`; opening, reading,
writing, mapping and locking remain prohibited by neverallow checks. Exact
`container_t` receives only the existing lock-use rights: `getattr`, `open`,
`read`, `write` and `lock`. No creation, replacement or relabel right follows.

Both enabled API and worker launchers must validate the fixed lock's no-follow
metadata and SELinux context and omit shared relabeling for that bind. The
worker reads only captured protected rendered server configuration to determine
the existing helper opt-in; it receives no helper projection, index, key or
policy-directory access. Disabled launches retain their existing arguments.
An API helper projection always preserves this lock label. The launcher does
not create, truncate, chmod, relabel or repair the lock.

The rootless guard observer brackets its unchanged original-inode/FLOCK
predicate with fixed-lock metadata/context checks under the existing mixed
effective credentials, restoring credentials on every exit. Require the exact
`object_r` role, dedicated type and `s0` range, stable identity and actual indexed
service ownership. Native guard observation keeps its existing label behavior.

## Rationale and alternatives

A dedicated coordination type permits the necessary metadata observation without
granting generic payload access. Preserving it in both launchers prevents a
worker restart from silently replacing the API's validated label. A read-only
bind would prevent application locking, and a separate lock would break the
single original-inode authority. Broad `container_file_t` grants, automatic
relabeling, replacing the original lock and weakening confinement were rejected.

Keep the existing fifteen-role version1 installation receipt and guard protocol
unchanged. The selected CIL, installed module checksum and kernel-policy digest
bind this policy extension; the two launchers and confined rootless observer
check the fixed lock directly. A configurable path/type or new receipt role
would add authority and format work without strengthening that fixed proof.

## Consequences and compatibility

Enabled rootless deployments require explicit root provisioning of the original
lock label, a fresh policy installation receipt and newly bound deployment/policy
records before restart. Missing, unsafe, recreated or incorrectly labelled locks
refuse launch/observation. Reboot or lock recreation requires fresh independent
provisioning. Known inactive guard observation keeps its existing behavior;
enabled application launch still validates the lock.

This adds no runtime dependency, helper operation, category grant, capability,
secret access, archive payload right or automatic activation. Disabled rootless
and native profiles remain supported. Actual enforcing startup, restart,
guarded status and metadata-only helper confinement remain required evidence.

## Evidence and relationships

Amends only the rootless archive-lock observation/provisioning policy in
[decision150](decision-150.md), preserving its original peer, process and guard
requirements. See [host administration](../host-administration.md),
[deployment provisioning](../web-ui/deployment.md),
[the launcher](../../scripts/container-service.py),
[the fixed observer](../../src/hfcache/host_policy.py) and
[the SELinux policy](../../packaging/selinux/hfcache-host-helper.cil).
