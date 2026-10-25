# Administration and host permissions

The web interface provides protected host status in unreleased source. Keep the
installed Cockpit interface until replacement acceptance and migration are
complete. Source availability does not change the running host's permissions.

The human administrator signs in with the configured browser Basic account.
That account is separate from service bearer credentials and host policy. Login
lets you view the interface; it cannot grant archive, Hub or host authority.

## Read the permission evidence

Administration displays the selected deployment, independent host-policy proof
and six effective categories: archive jobs, Hub sizing/diagnostics, control-state
previews, configuration, schedules and scheduled-observer control. An explicit
denial reason is part of each category. Rootless schedule and observer controls
stay denied while their fixed system-manager bindings are unproved.

Supported means the helper could verify the selected installed profile. Guarded
means the original read-only guard is held and archive actions are denied.
Unknown means required facts or binding could not be proved. Unavailable means
the helper cannot currently provide an authenticated bounded observation. Neither
unknown nor unavailable grants actions, implies an inactive service, or proves
an API/worker crash. A known absent guard grants nothing by itself.

Status does not show archive health or prove that a write would succeed. Domain
locks, storage guards, configured scope and policy remain final. An enabled
policy category also does not implement a host action whose endpoint is absent.
The verification timer is display-only.

Open **Administration** to view **Host administration**. **Refresh host status**
performs another bounded read; it never submits or retries an operation. Known
permission refusals display **Denied** with their reason; missing authority
displays **Unavailable**. **Allowed** describes the independently verified policy
category. This interface currently provides status reads; no configuration or
schedule mutation follows from displaying that category.

## Provision policy independently

A host administrator installs the selected immutable application/helper and
verifies their exact index before provisioning the independent policy. Keep the
legacy Cockpit policy separate. Do not copy true permissions into a new policy
without reviewing their intended scope. Begin with all categories denied, or a
reviewed configuration-only policy on a restricted host.

The policy, deployment index and revision key have fixed protected paths and
strict ownership/modes. The API cannot create or repair them. Follow the
[host contract](../host-administration.md) and
[deployment guide](deployment.md); the helper needs only its API-only Unix
directory mount, never a manager/engine socket or writable /etc mount.
Install the exact reviewed helper unit and entry together. Startup's bounded
ambient SETUID is temporary: the entry must clear all ambient/inheritable bits
before threads or children. Fixed read-only engine observation uses a separate
USER-only child with only namespace-local DAC_READ_SEARCH and SYS_ADMIN at
the fixed engine execution boundary (effective/permitted/bounding mask0x200004),
empty inheritable/ambient sets and locked securebits0xCE.
[Decision151](../adr/decision-151.md) supersedes the earlier SYS_ADMIN-only rule.
Read/search DAC bypass covers all reachable mapped-UID-and-GID inodes, not just
one metadata path; it grants no write or regular-file execute bypass and does
not replace SELinux. The daemon's initial-USER ceiling stays SETUID/SETGID; add
no initial-USER DAC. SELinux must never authorize DAC_OVERRIDE; require its bit
absent at verified steady/fixed-exec boundaries. Prove the masked MNT belongs
to initial USER and MNT-entry/unshare plus archive/Hub/IP and required inode/FD-alias
denials hold under the revised bits. The host observer
keeps initial USER and its original masked MNT view. Do not remove hardening or
substitute a broad Podman command when status is unavailable. A prototype info
result is not installed helper/API acceptance.

The host reader additionally requires the separately installed, enforcing
`hfcache_host_helper_t` SELinux policy from first exec, inherited by every helper
child. Install the exact selected CIL and fixed object labels, then independently
record the actual loaded module/kernel-policy and label facts in root-owned
`/etc/hfcache/host-helper-selinux.json`; the neutral index pins that receipt.
Archive/Hub/credential/container-secret object types must deny helper reads through
aliases as well as direct paths. Retain all masks, capability/namespace limits and
NoNewPrivileges. No policy/label installation or permission grant occurs on a
status read. Unsupported or stale policy/labels refuse. See the
[mandatory SELinux contract](../host-administration.md#mandatory-selinux-isolation).
Owned nonsecret alias-denial and full installed API/helper proof remain required;
earlier source/INFO checks alone do not close this requirement.

## Recover when status is unavailable

Refresh the bounded status read after the host administrator restores the exact
selected helper, policy and protected address binding. A normal helper restart
can replace its socket inside the existing protected parent. Replacing that
parent or changing deployment/boot identity requires restarting the API under
the reviewed deployment procedure. Do not relax ownership, disable SELinux or
substitute an endpoint with a matching UID.

Login, ordinary reads and original operation key/ID/result observation remain
available when host proof is down. A failed observation does not cancel accepted
work. Retain its original handle and reconcile read-only; do not submit another
operation to test whether the first one ran. See
[troubleshooting](troubleshooting.md) and [API recovery](../api.md#reconnect-after-lost-acknowledgement).
