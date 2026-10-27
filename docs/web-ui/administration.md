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
category. Displaying it never submits a configuration or schedule mutation.

The separate **Configuration and tags** panel composes the existing protected
configuration read, managed validation, sizing preview and guarded application
APIs. Its configuration-read/write grants and independent policy checks stand
on their own; host-read is not an additional gate. A visible **Allowed** status
does not bypass fresh request/execution checks. Follow the
[configuration workflow](configuration-and-tags.md) for one in-memory draft,
exact-base review and original-outcome recovery. Full schedule, observer and
journal forms remain a separate Administration UI package. Their fixed host APIs
have independent native provisioning and permission requirements below.

## Schedule, observer and diagnostic APIs

The [fixed host API](../api.md#fixed-host-actions-and-original-outcomes) validates
calendar and delay values with the installed systemd tools. A change uses the
fresh exact schedule revision and one original idempotency key. Replace/reset
reload the manager and restart only a previously active sync timer. Pause stops
that timer; resume starts it without enabling it. Persistent catch-up can start
the scheduled observer. Verification scheduling remains read-only, and these
actions never operate on the application target, API or worker.

Stopping the scheduled sync observer requires fresh evidence identifying that
original boot, service invocation and process. It sends SIGTERM only to the
retained original process. An accepted backend job and the observer's pending
handle survive independently. A stopped observer does not prove cancellation,
failure or completion of that job.

Native observer stop needs the separately provisioned confined observer profile.
An ordinary native installation can expose the real observer identity and allow
schedule changes while correctly denying stop with `profile-unproved`. The host
administrator must install and verify the fixed context fragment and dedicated
scheduled-state label; granting a policy bit alone is insufficient. An inactive
timer may be reported as `linked` when installed by an immutable unit symlink.
That state is not calendar enablement; retain the actual unit state and check its
enablement links independently.

After a lost reply, observe the original schedule/stop outcome with its original
key. Keep API receipt state separate from host certainty: a stored schedule does
not prove manager reload succeeded, and an acknowledged signal without observed
exit is unconfirmed. Never submit a replacement key to discover what happened.
Private pending records and uncertain outcomes require operator review, not
browser cleanup or automatic rollback.

Journal pages cover only the sync and verification observers. They are finite,
newest-first diagnostics with explicit gaps/truncation and a short-lived cursor.
Only closed event, level and run-ID fields are exposed. Empty or missing journal
data establishes no operation outcome. See [native provisioning](deployment.md#optional-native-schedule-and-observer-provisioning)
and [troubleshooting](troubleshooting.md#schedule-observer-and-journal-diagnostics).

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
